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

    def invoke(self, stage, function, *args, native=False, event_facts=None, **kwargs):
        self.emit(stage, 'entered', **(event_facts or {}))
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
        facts={}
        integer=lambda value:int(getattr(value,'value',value))
        if self._name=='cuMemcpyDtoH_v2':facts=dict(source_device=integer(args[1]),byte_count=integer(args[2]))
        elif self._name=='cuMemsetD8_v2':facts=dict(destination_device=integer(args[0]),value=integer(args[1]),byte_count=integer(args[2]))
        return self._journal.invoke(self._name, self._function, *args, native=True,event_facts=facts)


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
        result=journal.invoke('slang_build',original_build,*args,**kwargs)
        if os.environ.get('NIKKE_SLANG_GENERATION_CACHE'):
            paths,hashes=result
            from pathlib import Path
            from portable_generation_cache import audit_receipt
            receipt=json.loads(next(iter(paths.values())).with_name(Path(args[0]).stem+'.generation-cache.json').read_text())
            audit_receipt(receipt,hashes,paths)
            journal.emit('slang_generation_cache','verified',receipt=receipt)
        return result
    with contextlib.ExitStack() as stack:
        if os.environ.get('NIKKE_SLANG_GENERATION_CACHE'):
            original_run=backend.subprocess.run
            def compiler_run(command,*args,**kwargs):
                from pathlib import Path
                if command and Path(command[0]).name.lower() in ('slangc','slangc.exe'):
                    return journal.invoke('slang_compiler',original_run,command,*args,**kwargs)
                return original_run(command,*args,**kwargs)
            stack.enter_context(patch.object(backend.subprocess,'run',compiler_run))
        stack.enter_context(patch.object(backend, 'build', build))
        compile_name='compile_cuda_artifact' if hasattr(backend,'compile_cuda_artifact') else 'compile_cuda_ptx'
        if hasattr(backend,compile_name):
            original_compile=getattr(backend,compile_name)
            def compile_ptx(*args,**kwargs):
                artifact,receipt=journal.invoke('cuda_compile_artifact',original_compile,*args,**kwargs)
                journal.emit('cuda_compile_cache','verified',receipt=receipt)
                return artifact,receipt
            stack.enter_context(patch.object(backend,compile_name,compile_ptx))
        if hasattr(backend,'cuda_readback_file'):
            original_readback=backend.cuda_readback_file
            def readback(call,device_address,output_size,path):
                journal.emit('cuda_readback_file','entered',device_address=device_address,output_bytes=output_size,chunk_bytes=backend.READBACK_CHUNK_BYTES)
                try:receipt=original_readback(call,device_address,output_size,path)
                except BaseException as error:
                    journal.emit('cuda_readback_file','raised',exception=type(error).__name__);raise
                journal.emit('cuda_readback_file','returned',receipt=receipt)
                return receipt
            stack.enter_context(patch.object(backend,'cuda_readback_file',readback))
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
                cuda_linked_artifact_observed=any(valid_linked_artifact(r) for r in rows),
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
    streamed=any(r['stage']=='cuda_readback_file' for r in rows)
    stages=['nvrtcCompileProgram','cuLaunchKernel','cuCtxSynchronize']+([] if streamed else ['cuMemcpyDtoH_v2'])
    if not any(r['stage']=='nvrtcCompileProgram' for r in rows):
        hits=[(i,r) for i,r in enumerate(rows) if valid_cache_hit(r) or valid_linked_artifact(r)]
        if len(hits)!=1:return False
        previous=hits[0][0];stages=stages[1:]
    if any(r['stage']=='nvrtcCompileProgram' for r in rows) and any(valid_linked_artifact(r) for r in rows):return False
    for stage in stages:
        hits=[(i,r) for i,r in enumerate(rows) if r['stage']==stage]
        if (len(hits)!=2 or hits[0][1]['state']!='entered' or hits[1][1]['state']!='returned'
            or hits[1][1].get('return_code')!=0 or hits[0][0]<=previous):
            return False
        previous=hits[1][0]
    if streamed:
        try:return verify_streamed_readback(rows,previous)
        except (ValueError,KeyError,TypeError,OverflowError):return False
    return True


def verify_streamed_readback(rows,previous):
    # Bind every actual native copy to one complete, fixed-size file stream.
    from portable_backend import READBACK_CHUNK_BYTES
    markers=[(i,r) for i,r in enumerate(rows) if r['stage']=='cuda_readback_file']
    if len(markers)!=2 or [r['state'] for _,r in markers]!=['entered','returned'] or markers[0][0]<=previous:return False
    request=markers[0][1];receipt=markers[1][1]['receipt'];size=request['output_bytes'];address=request['device_address']
    if type(size) is not int or size<=0 or type(address) is not int or address<=0 or request['chunk_bytes']!=READBACK_CHUNK_BYTES:return False
    chunks=(size+READBACK_CHUNK_BYTES-1)//READBACK_CHUNK_BYTES
    if any(type(receipt[k]) is not int for k in ('output_bytes','chunk_bytes','chunks')) or receipt['output_bytes']!=size or receipt['chunk_bytes']!=READBACK_CHUNK_BYTES or receipt['chunks']!=chunks:return False
    digest=receipt['output_sha256']
    if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):return False
    copies=[(i,r) for i,r in enumerate(rows) if r['stage']=='cuMemcpyDtoH_v2']
    if len(copies)!=2*chunks:return False
    position=markers[0][0]
    for n in range(chunks):
        (first,a),(last,b)=copies[2*n:2*n+2];offset=n*READBACK_CHUNK_BYTES
        if not position<first<last<markers[1][0] or a['state']!='entered' or b['state']!='returned' or b.get('return_code')!=0:return False
        if a.get('source_device')!=address+offset or a.get('byte_count')!=min(READBACK_CHUNK_BYTES,size-offset):return False
        position=last
    zeros=[(i,r) for i,r in enumerate(rows) if r['stage']=='cuMemsetD8_v2']
    launch=next(i for i,r in enumerate(rows) if r['stage']=='cuLaunchKernel')
    if len(zeros)!=2 or [r['state'] for _,r in zeros]!=['entered','returned'] or zeros[1][1].get('return_code')!=0:return False
    cleanup=[(i,r) for i,r in enumerate(rows) if r['stage']=='cuCtxDestroy_v2']
    if len(cleanup)!=2 or [r['state'] for _,r in cleanup]!=['entered','returned'] or cleanup[1][1].get('return_code')!=0 or not markers[1][0]<cleanup[0][0]<cleanup[1][0]:return False
    a=zeros[0][1]
    compiler_end=max(i for i,r in enumerate(rows) if r['stage']=='nvrtcCompileProgram' and r['state']=='returned' or valid_cache_hit(r) or valid_linked_artifact(r))
    return bool(compiler_end<zeros[0][0]<zeros[1][0]<launch and a.get('destination_device')==address and a.get('value')==0 and a.get('byte_count')==size)


def valid_cache_hit(row):
    receipt=row.get('receipt',{})
    return (row.get('stage')=='cuda_compile_cache' and row.get('state')=='verified'
            and receipt.get('enabled') is True and receipt.get('hit') is True
            and isinstance(receipt.get('artifact_bytes'),int) and receipt['artifact_bytes']>0
            and all(isinstance(receipt.get(k),str) and len(receipt[k])==64
                    and all(c in '0123456789abcdef' for c in receipt[k]) for k in ('key','artifact_sha256')))



def valid_linked_artifact(row):
    if row.get('stage')!='cuda_linked_artifact_receipt':return False
    from portable_linked_artifact import valid_marker
    return valid_marker(row)
