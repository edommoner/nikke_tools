"""Shared Slang build + buffer transport. No effect or numeric game logic here.
Both backends execute the same entry, input words and output comparison.
"""
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import struct
import subprocess
import tempfile
import selectors
import time

ROOT = Path(__file__).resolve().parents[1]


def source_hashes(source):
    found = {}
    def visit(path):
        key = path.relative_to(ROOT).as_posix()
        if key in found:
            return
        raw = path.read_bytes()
        found[key] = hashlib.sha256(raw).hexdigest()
        for include in re.findall(rb'^\s*#include\s+"([^"]+)"', raw, re.M):
            visit((path.parent/include.decode()).resolve())
    visit(ROOT/source)
    return found


def build(source, entry):
    compiler_root = ROOT/f'.tools/slang-2026.20-{platform.system()}-{platform.machine()}'
    compiler = compiler_root/'bin'/('slangc.exe' if os.name == 'nt' else 'slangc')
    hashes = source_hashes(source)
    directory = ROOT/'research/portable-build'
    directory.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for target, suffix in [('cuda', 'cu'), ('metal', 'metal')]:
        output = directory/f'{Path(source).stem}.{suffix}'
        process = subprocess.run([str(compiler), str(ROOT/source), '-entry', entry,
                                  '-target', target, '-fp-mode', 'precise'], capture_output=True, timeout=90)
        if process.returncode:
            raise RuntimeError(process.stderr.decode('utf-8', 'replace'))
        # Multiple application requests may build the same immutable shader.
        # Publish atomically so another Swift process never reads a partial file.
        with tempfile.NamedTemporaryFile(dir=directory,delete=False) as temporary:
            temporary.write(process.stdout);temporary_path=Path(temporary.name)
        temporary_path.replace(output)
        outputs[target] = output
    if source_hashes(source) != hashes:
        raise RuntimeError('GPU sources changed during build; discard generated outputs')
    return outputs, hashes


def run_metal_command(command, *, compile_timeout=300, gpu_timeout=120):
    """Bound cold compilation separately from GPU execution; consume both pipes.

    The Swift adapter emits the dispatch marker just before command.commit().
    A compile/lock wait can never consume the subsequent GPU deadline.
    """
    stage='compile';deadline=time.monotonic()+compile_timeout
    chunks={'stdout':bytearray(),'stderr':bytearray()}
    with subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE) as process:
        with selectors.DefaultSelector() as selector:
            for name in chunks:
                stream=getattr(process,name);os.set_blocking(stream.fileno(),False)
                selector.register(stream,selectors.EVENT_READ,name)
            try:
                while selector.get_map():
                    remaining=deadline-time.monotonic()
                    if remaining<=0:
                        raise RuntimeError('Metal timeout ('+stage+' phase): '+chunks['stderr'].decode('utf-8','replace').strip())
                    for key,_ in selector.select(min(remaining,.25)):
                        data=os.read(key.fd,65536)
                        if not data:selector.unregister(key.fileobj);continue
                        chunks[key.data].extend(data)
                        if stage=='compile' and b'portable_stage=gpu_dispatch\n' in chunks['stderr']:
                            stage='gpu';deadline=time.monotonic()+gpu_timeout
                code=process.wait(timeout=max(.001,deadline-time.monotonic()))
            except subprocess.TimeoutExpired as error:
                process.kill();process.wait()
                raise RuntimeError('Metal timeout ('+stage+' phase): '+chunks['stderr'].decode('utf-8','replace').strip()) from error
            except BaseException:
                process.kill();process.wait();raise
    return subprocess.CompletedProcess(command,code,chunks['stdout'].decode('utf-8','replace'),chunks['stderr'].decode('utf-8','replace'))


def execute(source, entry, packed, input_words, output_words, backend='metal'):
    if backend not in ('metal', 'cuda'):
        raise ValueError('Explicit metal or cuda backend required; no CPU fallback')
    if type(input_words) is not int or type(output_words) is not int or not 1<=input_words<=131072 or not 1<=output_words<=131072:
        raise ValueError('Invalid portable word strides')
    count, = struct.unpack_from('<I', packed)
    if not 1 <= count <= 65536 or 1+count*input_words>0xffffffff or count*output_words>0xffffffff or len(packed) != (1+count*input_words)*4:
        raise ValueError('Invalid portable wire dimensions')
    outputs, hashes = build(source, entry)
    directory = ROOT/'research/portable-build'
    with tempfile.TemporaryDirectory(prefix='dispatch-', dir=directory) as tmp:
        input_path, output_path = Path(tmp)/'input.bin', Path(tmp)/'output.bin'
        input_path.write_bytes(packed)
        if backend == 'metal':
            if platform.system() != 'Darwin':
                raise RuntimeError('Metal requires macOS')
            process = run_metal_command(['swift', str(ROOT/'scripts/run-metal-probe.swift'),
                                         str(outputs['metal']), str(input_path), str(output_path),
                                         entry, str(input_words), str(output_words)])
            if process.returncode:
                raise RuntimeError(process.stderr or process.stdout)
            raw, transport = output_path.read_bytes(), json.loads(process.stdout)
            transport.update(compile_timeout_seconds=300,gpu_timeout_seconds=120)
        else:
            raw, transport = execute_cuda(outputs['cuda'], entry, packed, count*output_words*4, count)
    if len(raw) != count*output_words*4 or hashes != source_hashes(source):
        raise RuntimeError('Invalid GPU output or source changed during execution')
    return raw, dict(transport=transport, source_sha256=hashes,
                    generated_sha256={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in outputs.items()},
                    input_sha256=hashlib.sha256(packed).hexdigest(), output_sha256=hashlib.sha256(raw).hexdigest(),
                    gpu_execution_verified=True, backend=backend)


def execute_cuda(source, entry, packed, output_size, count):
    """Opt-in, single short dispatch. Never installs CUDA or starts a monitor.
    The pinned Slang StructuredBuffer ABI is pointer + size_t; validate the
    actual constant-symbol size before copying. NVIDIA execution pending.
    """
    if os.name != 'nt':
        raise RuntimeError('This CUDA NVRTC adapter currently requires Windows')
    cuda_bin = Path(os.environ.get('CUDA_PATH', r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.3'))/'bin'
    with os.add_dll_directory(str(cuda_bin)):
        lib = C.WinDLL(str(next(cuda_bin.glob('nvrtc64_*.dll'))))
        signatures = dict(nvrtcCreateProgram=[C.POINTER(C.c_void_p),C.c_char_p,C.c_char_p,C.c_int,C.c_void_p,C.c_void_p],
                          nvrtcCompileProgram=[C.c_void_p,C.c_int,C.POINTER(C.c_char_p)],
                          nvrtcGetProgramLogSize=[C.c_void_p,C.POINTER(C.c_size_t)], nvrtcGetPTXSize=[C.c_void_p,C.POINTER(C.c_size_t)],
                          nvrtcGetProgramLog=[C.c_void_p,C.c_void_p], nvrtcGetPTX=[C.c_void_p,C.c_void_p],
                          nvrtcDestroyProgram=[C.POINTER(C.c_void_p)])
        for name, signature in signatures.items():
            getattr(lib,name).argtypes=signature; getattr(lib,name).restype=C.c_int
        def check(code):
            if code: raise RuntimeError(f'NVRTC error {code}')
        program = C.c_void_p()
        try:
            check(lib.nvrtcCreateProgram(C.byref(program),source.read_bytes(),b'portable.cu',0,None,None))
            options = [b'--std=c++17',b'--gpu-architecture=compute_86',b'--fmad=false']
            code=lib.nvrtcCompileProgram(program,len(options),(C.c_char_p*len(options))(*options))
            size=C.c_size_t(); check(lib.nvrtcGetProgramLogSize(program,C.byref(size)))
            log=C.create_string_buffer(size.value);check(lib.nvrtcGetProgramLog(program,log))
            if code: raise RuntimeError(log.value.decode('utf-8','replace'))
            check(lib.nvrtcGetPTXSize(program,C.byref(size)));ptx=C.create_string_buffer(size.value);check(lib.nvrtcGetPTX(program,ptx))
        finally:
            if program: lib.nvrtcDestroyProgram(C.byref(program))
    driver=C.WinDLL('nvcuda.dll')
    signatures=dict(cuInit=[C.c_uint],cuDeviceGet=[C.POINTER(C.c_int),C.c_int],cuDeviceGetName=[C.c_char_p,C.c_int,C.c_int],
        cuCtxCreate_v2=[C.POINTER(C.c_void_p),C.c_uint,C.c_int],cuCtxDestroy_v2=[C.c_void_p],
        cuModuleLoadData=[C.POINTER(C.c_void_p),C.c_void_p],cuModuleGetFunction=[C.POINTER(C.c_void_p),C.c_void_p,C.c_char_p],
        cuModuleGetGlobal_v2=[C.POINTER(C.c_uint64),C.POINTER(C.c_size_t),C.c_void_p,C.c_char_p],
        cuMemAlloc_v2=[C.POINTER(C.c_uint64),C.c_size_t],cuMemcpyHtoD_v2=[C.c_uint64,C.c_void_p,C.c_size_t],
        cuMemcpyDtoH_v2=[C.c_void_p,C.c_uint64,C.c_size_t],cuCtxSynchronize=[],
        cuLaunchKernel=[C.c_void_p,*([C.c_uint]*7),C.c_void_p,C.c_void_p,C.c_void_p])
    for name, signature in signatures.items():
        getattr(driver,name).argtypes=signature;getattr(driver,name).restype=C.c_int
    def call(name,*args):
        code=getattr(driver,name)(*args)
        if code:raise RuntimeError(f'{name}: CUDA error {code}')
    context=C.c_void_p()
    call('cuInit',0);device=C.c_int();call('cuDeviceGet',C.byref(device),0)
    name=C.create_string_buffer(256);call('cuDeviceGetName',name,256,device)
    try:
        call('cuCtxCreate_v2',C.byref(context),0,device)
        module=C.c_void_p();function=C.c_void_p();call('cuModuleLoadData',C.byref(module),C.cast(ptx,C.c_void_p))
        call('cuModuleGetFunction',C.byref(function),module,entry.encode())
        inp=C.c_uint64();out=C.c_uint64();call('cuMemAlloc_v2',C.byref(inp),len(packed));call('cuMemAlloc_v2',C.byref(out),output_size)
        call('cuMemcpyHtoD_v2',inp,C.cast(C.c_char_p(packed),C.c_void_p),len(packed))
        zero=C.create_string_buffer(output_size);call('cuMemcpyHtoD_v2',out,C.cast(zero,C.c_void_p),output_size)
        global_ptr=C.c_uint64();global_size=C.c_size_t()
        call('cuModuleGetGlobal_v2',C.byref(global_ptr),C.byref(global_size),module,b'SLANG_globalParams')
        params=struct.pack('<QQQQ',inp.value,len(packed)//4,out.value,output_size//4)
        if global_size.value != len(params):raise RuntimeError('Unexpected Slang CUDA constant buffer ABI')
        call('cuMemcpyHtoD_v2',global_ptr,C.cast(C.c_char_p(params),C.c_void_p),len(params))
        started=time.perf_counter();call('cuLaunchKernel',function,count,1,1,1,1,1,0,None,None,None);call('cuCtxSynchronize')
        elapsed=time.perf_counter()-started
        output=C.create_string_buffer(output_size);call('cuMemcpyDtoH_v2',output,out,output_size)
        return output.raw,dict(backend='cuda',device=name.value.decode(),cases=count,command_status='completed',host_dispatch_seconds=elapsed)
    finally:
        if context:call('cuCtxDestroy_v2',context)
