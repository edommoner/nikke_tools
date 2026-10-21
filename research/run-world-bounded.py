"""Bound one shared world suite independently; preserve phase evidence on timeout."""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'app'), str(ROOT/'research')]
from portable_phase_audit import Journal, observe, summarize


class WindowsJob:
    """Kill only this validation tree, including pipe-holding descendants."""
    def __init__(self, process):
        self.process = process
        self.termination_waited = False
        self.termination_attempted = False
        self.assigned = False
        from ctypes import wintypes as W
        class Basic(C.Structure):
            _fields_ = [('process_time', C.c_int64), ('job_time', C.c_int64),
                        ('flags', C.c_uint32), ('min_ws', C.c_size_t), ('max_ws', C.c_size_t),
                        ('active_limit', C.c_uint32), ('affinity', C.c_size_t),
                        ('priority', C.c_uint32), ('scheduling', C.c_uint32)]
        class IO(C.Structure):
            _fields_ = [(n, C.c_uint64) for n in ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]
        class Extended(C.Structure):
            _fields_ = [('basic', Basic), ('io', IO), ('process_mem', C.c_size_t),
                        ('job_mem', C.c_size_t), ('peak_process', C.c_size_t), ('peak_job', C.c_size_t)]
        self.limit_info_type = Extended
        self.dll = C.WinDLL('kernel32', use_last_error=True)
        signatures = dict(CreateJobObjectW=([C.c_void_p, W.LPCWSTR], W.HANDLE),
                          SetInformationJobObject=([W.HANDLE, C.c_int, C.c_void_p, W.DWORD], W.BOOL),
                          AssignProcessToJobObject=([W.HANDLE, W.HANDLE], W.BOOL),
                          OpenProcess=([W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
                          TerminateJobObject=([W.HANDLE, W.UINT], W.BOOL),
                          QueryInformationJobObject=([W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)], W.BOOL),
                          CloseHandle=([W.HANDLE], W.BOOL))
        for name, (args, result) in signatures.items():
            fn = getattr(self.dll, name); fn.argtypes = args; fn.restype = result
        self.handle = self.dll.CreateJobObjectW(None, None)
        if not self.handle:
            raise C.WinError(C.get_last_error())
        try:
            limits = Extended(); limits.basic.flags = 0x2000  # KILL_ON_JOB_CLOSE
            if not self.dll.SetInformationJobObject(self.handle, 9, C.byref(limits), C.sizeof(limits)):
                raise C.WinError(C.get_last_error())
            handle = self.dll.OpenProcess(0x0101, False, process.pid)  # SET_QUOTA | TERMINATE
            if not handle:
                raise C.WinError(C.get_last_error())
            try:
                if not self.dll.AssignProcessToJobObject(self.handle, handle):
                    raise C.WinError(C.get_last_error())
                self.assigned = True
            finally:
                self.dll.CloseHandle(handle)
        except BaseException:
            self.close()
            raise

    def terminate_and_wait(self, timeout=5):
        """End only the owned validation tree, retaining its queryable handle."""
        if not self.handle or self.termination_waited:
            return
        deadline = time.monotonic()+timeout
        self.termination_attempted = True
        if not self.dll.TerminateJobObject(self.handle, 1):
            raise C.WinError(C.get_last_error())
        if getattr(self, 'assigned', True):
            self.process.wait(timeout=max(.001, deadline-time.monotonic()))
        # Query the process-list header; ERROR_MORE_DATA still returns a count.
        while True:
            buffer = C.create_string_buffer(8+64*C.sizeof(C.c_size_t))
            returned = C.c_ulong()
            success = self.dll.QueryInformationJobObject(self.handle, 3, buffer, len(buffer), C.byref(returned))
            if not success and C.get_last_error()!=234:
                raise C.WinError(C.get_last_error())
            if int.from_bytes(buffer.raw[4:8], 'little')==0:
                self.termination_waited = True
                return
            if time.monotonic()>=deadline:
                raise RuntimeError('Validation Job did not empty within cleanup budget')
            time.sleep(min(.01, max(0, deadline-time.monotonic())))

    def close(self):
        if self.handle:
            try:
                if not self.termination_attempted:
                    self.terminate_and_wait()
            finally:
                handle, self.handle = self.handle, None
                if not self.dll.CloseHandle(handle):
                    raise C.WinError(C.get_last_error())


def run_bounded(command, folder, timeout, *, cwd=None, env=None, before_gate=None, after_wait=None):
    started = time.perf_counter()
    job = None
    process = None
    timed_out = False
    failure = None
    cleanup_error = None
    child_code = None
    gate = folder/'start.json'
    if gate.exists():
        raise ValueError('Fresh capture directory required')
    observation_error = None
    wait_completed_ns = None
    with (folder/'stdout.log').open('wb') as stdout, (folder/'stderr.log').open('wb') as stderr:
        try:
            options = dict(stdout=stdout, stderr=stderr, cwd=cwd or ROOT, env=env)
            if os.name == 'nt':
                options['creationflags'] = subprocess.BELOW_NORMAL_PRIORITY_CLASS
            else:
                options['start_new_session'] = True
            process = subprocess.Popen(command, **options)
            if os.name == 'nt':
                job = WindowsJob(process)
            # Child cannot compile/load CUDA before containment succeeds.
            if before_gate is not None:
                before_gate()
            gate.write_text('{}\n')
            child_code = process.wait(timeout=max(.001, timeout-(time.perf_counter()-started)))
        except subprocess.TimeoutExpired:
            timed_out = True
        except BaseException as error:
            failure = type(error).__name__+': '+str(error)
        finally:
            try:
                if job is not None:
                    job.close()
                elif process is not None and os.name != 'nt':
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if process is not None:
                    if process.poll() is None:
                        process.kill()
                    # The Job cleanup already consumed its one five-second budget.
                    process.wait(timeout=0 if job is not None else 5)
            except BaseException as error:
                cleanup_error = type(error).__name__+': '+str(error)
            finally:
                wait_completed_ns = time.time_ns()
                if after_wait is not None:
                    try:
                        after_wait()
                    except BaseException as error:
                        observation_error = type(error).__name__+': '+str(error)
    facts = dict(passed=not timed_out and failure is None and cleanup_error is None and child_code == 0,
                 timed_out=timed_out, timeout_seconds=timeout, elapsed_seconds=time.perf_counter()-started,
                 child_exit_code=child_code, final_child_exit_code=process.poll() if process is not None else None,
                 error=failure, cleanup_error=cleanup_error, cleanup_wait_seconds=5,
                 observation_error=observation_error, wait_completed_unix_ns=wait_completed_ns,
                 below_normal_priority=os.name == 'nt', phase=summarize(folder/'phases.jsonl'),
                 gpu_retry_count=0, full_character_verified=0, full_goal_complete=False)
    (folder/'execution.json').write_text(json.dumps(facts, indent=2)+'\n')
    return facts


def child(folder, backend):
    deadline = time.monotonic()+10
    while not (folder/'start.json').exists():
        if time.monotonic() >= deadline:
            raise RuntimeError('Containment gate not released; no GPU work started')
        time.sleep(.02)
    import portable_backend
    journal = Journal(folder/'phases.jsonl')
    with observe(portable_backend, journal):
        sys.argv = ['verify-world-suite.py', '--backend', backend, '--report', str(folder/'world-report.json')]
        journal.invoke('shared_world_suite', runpy.run_path, str(ROOT/'research/verify-world-suite.py'), run_name='__main__')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', choices=('metal', 'cuda'), required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--_child', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.timeout <= 180:
        parser.error('Timeout must be 1..180 seconds')
    folder = args.capture.resolve()
    if args._child:
        child(folder, args.backend)
        return
    folder.mkdir(parents=True, exist_ok=False)
    from portable_backend import source_hashes
    paths = ['research/run-world-bounded.py', 'research/portable_phase_audit.py',
             'research/verify-world-suite.py', 'research/portable-world-suite-golden.json',
             'app/portable_backend.py']
    manifest = dict(source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                    backend=args.backend, world_inputs=49,
                    observer_and_driver_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
                    gpu_source_sha256=source_hashes('gpu/world_frame_entry.slang'),
                    strategy='world-only independent budget; unchanged shared49 suite; durable native boundaries; contained process tree')
    (folder/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    command = [sys.executable, str(Path(__file__).resolve()), '--_child', '--backend', args.backend,
               '--capture', str(folder), '--timeout', str(args.timeout)]
    facts = run_bounded(command, folder, args.timeout)
    print(json.dumps(facts))
    raise SystemExit(0 if facts['passed'] else 124 if facts['timed_out'] else 1)


if __name__ == '__main__':
    main()
