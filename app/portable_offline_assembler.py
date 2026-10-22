"""Pinned standalone PTX assembly. No CUDA/NVRTC API, source rewriting or fallback."""
import ctypes as C
import hashlib,json,os,re,subprocess,time,types
from pathlib import Path
TOOL_SHA256='0183c5b1fdecc69234597efac421eca4670a3f6ed6ed028ff6afb85d06f3efb8'
WHEEL_SHA256='aadd9fb307352bbcd5bc89b5f98c10cd78000915094882d97321f5fe36441742'
TOOL_VERSION='12.4.131'
OPTIONS=['--gpu-name=sm_86','--opt-level=1','--fmad=false','--verbose']


def digest(raw):return hashlib.sha256(raw).hexdigest()

def validate_tool(path):
    raw=Path(path).read_bytes()
    if digest(raw)!=TOOL_SHA256 or not raw.startswith(b'MZ'):raise ValueError('Standalone assembler is not the pinned NVIDIA component')
    return dict(version=TOOL_VERSION,sha256=TOOL_SHA256,wheel_sha256=WHEEL_SHA256,bytes=len(raw))

def validate_ptx(raw):
    version=re.search(rb'(?m)^\s*\.version\s+(\d+)\.(\d+)\s*$',raw)
    target=re.search(rb'(?m)^\s*\.target\s+(sm_\d+)[^\n]*$',raw)
    if not version or tuple(map(int,version.groups()))!=(8,4) or not target or target[1]!=b'sm_86':
        raise ValueError('Standalone assembly requires unchanged PTX8.4 targeting sm_86')
    return dict(version='8.4',target='sm_86',bytes=len(raw),sha256=digest(raw))

def inspect_process(process):
    # NULL job queries the calling validation process's current JobObject.
    # The assembler inherits that Job at CreateProcess, before its first opcode.
    from windows_validation_observer import inspect_job
    from ctypes import wintypes as W
    dll=C.WinDLL('kernel32',use_last_error=True)
    dll.CloseHandle.argtypes=[W.HANDLE];dll.CloseHandle.restype=W.BOOL
    job=types.SimpleNamespace(dll=dll,handle=None)
    return inspect_job(job,process)

def contained(snapshot,harness_pid,assembler_pid):
    return bool(type(assembler_pid) is int and assembler_pid>0 and assembler_pid!=harness_pid and snapshot.get('wrapper_pid')==harness_pid and snapshot.get('child_pid')==assembler_pid and snapshot.get('child_ppid')==harness_pid
        and snapshot.get('child_creation_filetime_ticks') and snapshot.get('parent_observation')=='os_process_snapshot'
        and set(snapshot.get('job_members',[]))=={harness_pid,assembler_pid})

def run(capture,tool,ptx,origin,*,journal,popen=None,inspector=None):
    capture=Path(capture).resolve();tool=Path(tool).resolve();tool_info=validate_tool(tool);ptx_info=validate_ptx(ptx)
    input_path=capture/'input.ptx';partial=capture/'compiled.cubin.partial';output=capture/'compiled.cubin'
    if partial.exists() or output.exists():raise FileExistsError('Assembler output already exists')
    with input_path.open('xb') as stream:stream.write(ptx);stream.flush();os.fsync(stream.fileno())
    journal.emit('offline_ptxas_tool','verified',tool=tool_info)
    journal.emit('offline_ptxas_input','verified',input=ptx_info)
    argv=[str(tool),*OPTIONS,str(input_path),'-o',str(partial)]
    journal.emit('offline_ptxas','entered',argv=argv,tool_sha256=tool_info['sha256'])
    creator=popen or subprocess.Popen;reader=inspector or inspect_process
    started=time.perf_counter();process=None
    try:
        with (capture/'assembler.stdout.log').open('xb') as stdout,(capture/'assembler.stderr.log').open('xb') as stderr:
            process=creator(argv,cwd=capture,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,shell=False,
                creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name=='nt' else 0)
            snapshot=reader(process)
            if not contained(snapshot,os.getpid(),process.pid):raise RuntimeError('Standalone assembler is not in the validation Job')
            journal.emit('offline_ptxas_child','verified',inspection=snapshot)
            code=process.wait(timeout=55)
        elapsed=time.perf_counter()-started
        journal.emit('offline_ptxas','returned',return_code=code,elapsed_seconds=elapsed)
        if code:raise RuntimeError('Standalone ptxas failed with exit code '+str(code))
        if validate_tool(tool)!=tool_info or input_path.read_bytes()!=ptx:raise ValueError('Assembler inputs changed during execution')
        artifact=partial.read_bytes()
        if not artifact.startswith(b'\x7fELF') or len(artifact)<64:raise ValueError('Standalone assembler did not produce a complete ELF artifact')
        if output.exists():raise FileExistsError('Assembler artifact already exists')
        with partial.open('r+b') as stream:os.fsync(stream.fileno())
        partial.rename(output)
        identity=dict(schema=1,provider='offline-ptxas',artifact='cubin',tool=tool_info,options=OPTIONS,
            input=ptx_info,upstream_cache_key=origin['cache_key'],upstream_cuda_sha256=origin['cuda_sha256'])
        receipt=dict(identity=identity,key=digest(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()),
            artifact_bytes=len(artifact),artifact_sha256=digest(artifact),elapsed_seconds=elapsed)
        journal.emit('offline_assembly_receipt','verified',receipt=receipt)
        return receipt
    except BaseException as error:
        journal.emit('offline_assembly_failure','raised',exception=type(error).__name__)
        if process is not None and process.poll() is None:
            process.terminate();process.wait(timeout=5)
        raise
