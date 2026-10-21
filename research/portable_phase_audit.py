"""Opt-in research observer; never changes shader, compiler options or buffers."""
import contextlib
import ctypes
import json
import os
import time
from unittest.mock import patch


class Journal:
    def __init__(self, path):
        self.path = path

    def emit(self, stage, state, **facts):
        row = dict(stage=stage, state=state, monotonic_ns=time.monotonic_ns(),
                   wall_time_ns=time.time_ns(), pid=os.getpid(), **facts)
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, sort_keys=True)+'\n')
            stream.flush()
            os.fsync(stream.fileno())

    def invoke(self, stage, function, *args, native=False, **kwargs):
        self.emit(stage, 'entered')
        try:
            result = function(*args, **kwargs)
        except BaseException as error:
            self.emit(stage, 'raised', exception=type(error).__name__)
            raise
        self.emit(stage, 'returned', **({'return_code': int(result)} if native else {}))
        return result


class NativeFunction:
    def __init__(self, function, name, journal):
        object.__setattr__(self, '_function', function)
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '_journal', journal)

    def __getattr__(self, name):
        return getattr(self._function, name)

    def __setattr__(self, name, value):
        setattr(self._function, name, value)

    def __call__(self, *args):
        return self._journal.invoke(self._name, self._function, *args, native=True)


class NativeLibrary:
    def __init__(self, library, journal):
        self.library, self.journal, self.functions = library, journal, {}

    def __getattr__(self, name):
        if name not in self.functions:
            self.functions[name] = NativeFunction(getattr(self.library, name), name, self.journal)
        return self.functions[name]


@contextlib.contextmanager
def observe(backend, journal):
    """Wrap actual boundaries; a launch *entry* alone proves no submission."""
    original_build = backend.build
    def build(*args, **kwargs):
        return journal.invoke('slang_build', original_build, *args, **kwargs)
    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(backend, 'build', build))
        compile_name='compile_cuda_artifact' if hasattr(backend,'compile_cuda_artifact') else 'compile_cuda_ptx'
        if hasattr(backend,compile_name):
            original_compile=getattr(backend,compile_name)
            def compile_ptx(*args,**kwargs):
                artifact,receipt=journal.invoke('cuda_compile_artifact',original_compile,*args,**kwargs)
                journal.emit('cuda_compile_cache','verified',receipt=receipt)
                return artifact,receipt
            stack.enter_context(patch.object(backend,compile_name,compile_ptx))
        if os.name == 'nt':
            original_dll = ctypes.WinDLL
            def library(*args, **kwargs):
                return NativeLibrary(original_dll(*args, **kwargs), journal)
            stack.enter_context(patch.object(ctypes, 'WinDLL', library))
        yield


def summarize(path):
    rows = []
    if path.exists():
        lines = path.read_text().splitlines()
        for index, line in enumerate(lines):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # A killed process may leave only the final append incomplete.
                if index != len(lines)-1:
                    raise
    returned = lambda stage: any(r['stage'] == stage and r['state'] == 'returned'
                                 and r.get('return_code') == 0 for r in rows)
    return dict(events=len(rows), last_event=rows[-1] if rows else None,
                nvrtc_compile_returned_success=returned('nvrtcCompileProgram'),
                cuda_compile_cache_hit_verified=any(valid_cache_hit(r) for r in rows),
                cuda_launch_returned_success=returned('cuLaunchKernel'),
                cuda_synchronize_returned_success=returned('cuCtxSynchronize'),
                cuda_readback_returned_success=returned('cuMemcpyDtoH_v2'),
                scope='Observed API returns only; full output verification requires the shared suite report')


def verify_cuda_trace(rows, *, pid=None):
    """Validate ordered successful native boundaries, never an entry marker alone."""
    if not rows or any(row['state']=='raised' for row in rows):
        return False
    if any(a['monotonic_ns']>b['monotonic_ns'] for a,b in zip(rows,rows[1:])):
        return False
    if pid is not None and {row['pid'] for row in rows}!={pid}:
        return False
    previous=-1
    stages=['nvrtcCompileProgram','cuLaunchKernel','cuCtxSynchronize','cuMemcpyDtoH_v2']
    if not any(r['stage']=='nvrtcCompileProgram' for r in rows):
        hits=[(i,r) for i,r in enumerate(rows) if valid_cache_hit(r)]
        if len(hits)!=1:return False
        previous=hits[0][0];stages=stages[1:]
    for stage in stages:
        hits=[(i,r) for i,r in enumerate(rows) if r['stage']==stage]
        if (len(hits)!=2 or hits[0][1]['state']!='entered' or hits[1][1]['state']!='returned'
            or hits[1][1].get('return_code')!=0 or hits[0][0]<=previous):
            return False
        previous=hits[1][0]
    return True


def valid_cache_hit(row):
    receipt=row.get('receipt',{})
    return (row.get('stage')=='cuda_compile_cache' and row.get('state')=='verified'
            and receipt.get('enabled') is True and receipt.get('hit') is True
            and isinstance(receipt.get('artifact_bytes'),int) and receipt['artifact_bytes']>0
            and all(isinstance(receipt.get(k),str) and len(receipt[k])==64
                    and all(c in '0123456789abcdef' for c in receipt[k]) for k in ('key','artifact_sha256')))
