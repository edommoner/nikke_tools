"""CPU fault injection: failed API calls cannot become successful GPU evidence."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'research'),str(ROOT/'app')]
from portable_phase_audit import Journal, NativeLibrary, observe, observe_generation, summarize
spec = importlib.util.spec_from_file_location('world_bounded', ROOT/'research/run-world-bounded.py')
bounded = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bounded)


class AuditTests(unittest.TestCase):
    def test_function_duration_excludes_its_own_journal_writes_and_no_unfinished_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'timed.jsonl';journal=Journal(path)
            with patch('portable_phase_audit.time.perf_counter_ns',side_effect=[100,1000000100]):
                self.assertEqual(journal.invoke('actual',lambda:7),7)
            journal.emit('unfinished','entered')
            report=summarize(path)
            self.assertEqual(report['timed_calls'],[dict(stage='actual',pid=os.getpid(),state='returned',elapsed_seconds=1.)])
            self.assertEqual(report['last_event']['stage'],'unfinished')
            self.assertFalse(report['cuda_launch_returned_success'])

    def test_generation_observer_preserves_arguments_results_and_restores_on_failure(self):
        import portable_generation_cache as cache
        import portable_resident_layout as layout
        import portable_scope_snapshot_audit as scope
        modules=[(cache,n) for n in ('identity','validate_pair','read_entry','atomic','reflection_plan','verify_cuda_layout_assertions')]+[(layout,'reflection_plan'),(scope,'audit')]
        originals={(m,n):getattr(m,n) for m,n in modules}
        token=object();received=[]
        def identity(*args,**kwargs):received.append((args,kwargs));return token
        with tempfile.TemporaryDirectory() as directory,patch.object(cache,'identity',identity):
            path=Path(directory)/'generation.jsonl'
            with self.assertRaisesRegex(RuntimeError,'injected'),observe_generation(Journal(path)):
                self.assertIs(cache.identity(token,entry='unchanged'),token)
                self.assertEqual(received,[((token,),{'entry':'unchanged'})])
                raise RuntimeError('injected')
            self.assertIs(cache.identity,identity)
            rows=[json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual([(r['stage'],r['state']) for r in rows],[('slang_generation_identity','entered'),('slang_generation_identity','returned')])
            self.assertFalse(summarize(path)['cuda_launch_returned_success'])
        for (module,name),original in originals.items():self.assertIs(getattr(module,name),original)

    def test_generation_audit_failure_remains_failure(self):
        import portable_generation_cache as cache
        def fail(*args):raise ValueError('bad pair')
        with tempfile.TemporaryDirectory() as directory,patch.object(cache,'validate_pair',fail):
            path=Path(directory)/'generation.jsonl'
            with self.assertRaisesRegex(ValueError,'bad pair'),observe_generation(Journal(path)):
                cache.validate_pair({},'portableEvents')
            self.assertIs(cache.validate_pair,fail)
            rows=[json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual([(r['stage'],r['state']) for r in rows],[('slang_generation_validate_pair','entered'),('slang_generation_validate_pair','raised')])

    def test_native_proxy_preserves_signature_arguments_result_and_failed_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'phases.jsonl'
            argument = object()
            received = []
            def launch(*args):
                received.append(args)
                return 701
            lib = NativeLibrary(types.SimpleNamespace(cuLaunchKernel=launch), Journal(path))
            lib.cuLaunchKernel.argtypes = ['exact signature']
            lib.cuLaunchKernel.restype = int
            self.assertIs(lib.cuLaunchKernel, lib.cuLaunchKernel)
            self.assertEqual(lib.cuLaunchKernel(argument), 701)
            self.assertIs(received[0][0], argument)
            self.assertEqual(launch.argtypes, ['exact signature'])
            self.assertIs(launch.restype, int)
            self.assertFalse(summarize(path)['cuda_launch_returned_success'])

    def test_exception_keeps_last_actual_stage_and_observer_restores_backend(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'phases.jsonl'
            def fail(*args):
                raise RuntimeError('injected compilation failure')
            backend = types.SimpleNamespace(build=fail)
            with self.assertRaises(RuntimeError), observe(backend, Journal(path)):
                backend.build('unchanged source', 'unchanged entry')
            self.assertIs(backend.build, fail)
            report = summarize(path)
            self.assertEqual(report['last_event']['stage'], 'slang_build')
            self.assertEqual(report['last_event']['state'], 'raised')
            self.assertFalse(report['cuda_launch_returned_success'])

    def test_successful_launch_alone_does_not_prove_sync_or_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'phases.jsonl'
            journal = Journal(path)
            journal.invoke('nvrtcCompileProgram', lambda: 0, native=True)
            journal.invoke('cuLaunchKernel', lambda: 0, native=True)
            journal.emit('cuCtxSynchronize', 'entered')
            with path.open('a') as stream:
                stream.write('{"interrupted final append')
            report = summarize(path)
            self.assertTrue(report['nvrtc_compile_returned_success'])
            self.assertTrue(report['cuda_launch_returned_success'])
            self.assertFalse(report['cuda_synchronize_returned_success'])
            self.assertFalse(report['cuda_readback_returned_success'])

    def test_timeout_preserves_phase_and_elapsed_and_terminates_descendants(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            code = """
import subprocess,sys,time,pathlib
sys.path.insert(0,sys.argv[2])
from portable_phase_audit import Journal
p=pathlib.Path(sys.argv[1])
while not (p/'start.json').exists():time.sleep(.01)
Journal(p/'phases.jsonl').emit('nvrtcCompileProgram','entered')
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
(p/'descendant.pid').write_text(str(child.pid))
time.sleep(60)
"""
            facts = bounded.run_bounded([sys.executable, '-c', code, str(folder), str(ROOT/'research')], folder, 1)
            self.assertTrue(facts['timed_out'])
            self.assertFalse(facts['passed'])
            self.assertIsNotNone(facts['final_child_exit_code'])
            self.assertIsNone(facts['cleanup_error'])
            self.assertGreaterEqual(facts['elapsed_seconds'], 1)
            self.assertLess(facts['elapsed_seconds'], 7)
            self.assertEqual(facts['phase']['last_event']['stage'], 'nvrtcCompileProgram')
            self.assertFalse(facts['phase']['cuda_launch_returned_success'])
            pid = (folder/'descendant.pid').read_text()
            if os.name == 'nt':
                import ctypes as C
                from ctypes import wintypes as W
                dll = C.WinDLL('kernel32', use_last_error=True)
                dll.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]; dll.OpenProcess.restype = W.HANDLE
                dll.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]; dll.WaitForSingleObject.restype = W.DWORD
                dll.CloseHandle.argtypes = [W.HANDLE]; dll.CloseHandle.restype = W.BOOL
                handle = dll.OpenProcess(0x00100000, False, int(pid))
                if handle:
                    try:
                        self.assertEqual(dll.WaitForSingleObject(handle, 1000), 0)
                    finally:
                        dll.CloseHandle(handle)
                else:
                    self.assertEqual(C.get_last_error(), 87)  # Already gone; not access denied.
                self.assertTrue(facts['below_normal_priority'])
            else:
                for _ in range(20):
                    state = subprocess.run(['ps', '-p', pid, '-o', 'stat='], capture_output=True, text=True).stdout.strip()
                    if not state or state.startswith('Z'):
                        break
                    time.sleep(.05)
                self.assertTrue(not state or state.startswith('Z'), state)
            self.assertEqual(json.loads((folder/'execution.json').read_text())['timed_out'], True)

    def test_containment_failure_never_releases_gpu_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            with patch.object(bounded.subprocess, 'Popen', side_effect=OSError('cannot contain')):
                facts = bounded.run_bounded(['unused'], folder, 1)
            self.assertFalse(facts['passed'])
            self.assertFalse((folder/'start.json').exists())
            self.assertIsNone(facts['final_child_exit_code'])
            self.assertIn('OSError', facts['error'])


if __name__ == '__main__':
    unittest.main()
