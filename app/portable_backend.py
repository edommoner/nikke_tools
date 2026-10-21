"""Shared Slang build + buffer transport. No effect or numeric game logic here.
Both backends execute the same entry, input words and output comparison.
"""
import ctypes as C
import contextlib
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
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
MAX_INPUT_WORDS=131072
MAX_OUTPUT_WORDS=786432


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
    compiler_root = Path(os.environ.get('NIKKE_SLANG_ROOT', ROOT/f'.tools/slang-2026.20-{platform.system()}-{platform.machine()}'))
    compiler_root=compiler_root.resolve()
    compiler = compiler_root/'bin'/('slangc.exe' if os.name == 'nt' else 'slangc')
    hashes = source_hashes(source)
    resident=any(re.search(rb'^\s*#define\s+PORTABLE_RESIDENT_RUNTIME(?:\s|$)',(ROOT/name).read_bytes(),re.M) for name in hashes)
    directory = ROOT/'research/portable-build'
    directory.mkdir(parents=True, exist_ok=True)
    if resident:
        return _build_resident(compiler, source, entry, hashes, directory)
    outputs = {}
    for target, suffix in [('cuda', 'cu'), ('metal', 'metal')]:
        output = directory/f'{Path(source).stem}.{suffix}'
        process = subprocess.run([str(compiler), str(ROOT/source), '-entry', entry,
                                  '-target', target, '-fp-mode', 'precise', '-line-directive-mode', 'none',
                                  ], capture_output=True, timeout=90)
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


def _build_resident(compiler, source, entry, hashes, directory):
    """Validate fresh paired code/reflection before publishing any resident output."""
    from portable_resident_layout import reflection_plan,cuda_layout_assertions
    temporary_root=None
    if platform.system()=='Windows':
        # The bounded child intentionally redirects TEMP into its capture. Slang
        # can be denied native writes in Documents even when Python can publish
        # there. Keep compiler scratch in the user's OS temp, without changing
        # the child/parent environment or Windows security settings.
        local=os.environ.get('LOCALAPPDATA')
        if not local or not Path(local).is_absolute():raise ValueError('Missing absolute LOCALAPPDATA for Slang scratch')
        temporary_root=Path(local)/'Temp'
        if not temporary_root.is_dir():raise ValueError('Windows Slang scratch directory missing')
    with tempfile.TemporaryDirectory(prefix='nikke-resident-build-', dir=temporary_root) as tmp:
        staged={}
        for target,suffix in [('cuda','cu'),('metal','metal')]:
            output=Path(tmp)/(Path(source).stem+'.'+suffix)
            reflection=Path(str(output)+'.reflection.json')
            process=subprocess.run([str(compiler),str(ROOT/source),'-entry',entry,
                '-target',target,'-fp-mode','precise','-line-directive-mode','none',
                '-o',str(output),'-reflection-json',str(reflection)],capture_output=True,timeout=90)
            diagnostic=process.stderr.decode('utf-8','replace').strip()
            if process.returncode:
                raise RuntimeError('Slang resident '+target+' generation failed: '+diagnostic)
            for path in (output,reflection):
                if not path.is_file() or not path.stat().st_size:
                    raise RuntimeError('Slang resident '+target+' artifact missing or empty: '+path.name+'; '+diagnostic)
            staged[target]=output
        plan=reflection_plan(staged,entry)
        staged['cuda'].write_bytes(cuda_layout_assertions(staged['cuda'].read_bytes(),plan))
        if source_hashes(source)!=hashes:
            raise RuntimeError('GPU sources changed during build; discard generated outputs')
        outputs={}
        for target,path in staged.items():
            output=directory/path.name
            # Python publishes on the destination filesystem, including when
            # the checkout and OS temp are on different volumes.
            for candidate,destination in ((Path(str(path)+'.reflection.json'),Path(str(output)+'.reflection.json')),(path,output)):
                with tempfile.NamedTemporaryFile(dir=directory,delete=False) as temporary:
                    temporary.write(candidate.read_bytes());temporary_path=Path(temporary.name)
                temporary_path.replace(destination)
            outputs[target]=output
    return outputs,hashes


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


def resident_plan(source,entry,outputs):
    if not any(re.search(rb'^\s*#define\s+PORTABLE_RESIDENT_RUNTIME(?:\s|$)',(ROOT/name).read_bytes(),re.M) for name in source_hashes(source)):return None
    from portable_resident_layout import reflection_plan
    return reflection_plan(outputs,entry)


def execute(source, entry, packed, input_words, output_words, backend='metal'):
    if backend not in ('metal', 'cuda'):
        raise ValueError('Explicit metal or cuda backend required; no CPU fallback')
    if type(input_words) is not int or type(output_words) is not int or not 1<=input_words<=MAX_INPUT_WORDS or not 1<=output_words<=MAX_OUTPUT_WORDS or output_words>524288 and output_words not in (655360,786432):
        raise ValueError('Invalid portable word strides')
    count, = struct.unpack_from('<I', packed)
    if not 1 <= count <= 65536 or 1+count*input_words>0xffffffff or count*output_words>0xffffffff or len(packed) != (1+count*input_words)*4:
        raise ValueError('Invalid portable wire dimensions')
    outputs, hashes = build(source, entry)
    resident=resident_plan(source,entry,outputs)
    directory = ROOT/'research/portable-build'
    with tempfile.TemporaryDirectory(prefix='dispatch-', dir=directory) as tmp:
        input_path, output_path = Path(tmp)/'input.bin', Path(tmp)/'output.bin'
        input_path.write_bytes(packed)
        if backend == 'metal':
            if platform.system() != 'Darwin':
                raise RuntimeError('Metal requires macOS')
            process = run_metal_command(['swift', str(ROOT/'scripts/run-metal-probe.swift'),
                                         str(outputs['metal']), str(input_path), str(output_path),
                                         entry, str(input_words), str(output_words),*([str(resident["stride"])] if resident else [])])
            if process.returncode:
                raise RuntimeError(process.stderr or process.stdout)
            raw, transport = output_path.read_bytes(), json.loads(process.stdout)
            transport.update(compile_timeout_seconds=300,gpu_timeout_seconds=120)
        else:
            raw, transport = execute_cuda(outputs['cuda'], entry, packed, count*output_words*4, count,**({'resident':resident} if resident else {}))
    if len(raw) != count*output_words*4 or hashes != source_hashes(source):
        raise RuntimeError('Invalid GPU output or source changed during execution')
    return raw, dict(**(dict(resident_runtime=resident) if resident else {}),transport=transport, source_sha256=hashes,
                    generated_sha256={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in outputs.items()},
                    input_sha256=hashlib.sha256(packed).hexdigest(), output_sha256=hashlib.sha256(raw).hexdigest(),
                    gpu_execution_verified=True, backend=backend)


def execute_batches(source, entry, batches, input_words, output_words, backend='metal'):
    """Sequential independent dispatches in one compiled GPU session.

    Wire inputs and readbacks remain separate; a failure never returns a partial
    success. Both adapters reuse their pipeline/context and two bounded buffers.
    """
    if backend not in ('metal','cuda'):raise ValueError('Explicit metal or cuda backend required; no CPU fallback')
    if type(input_words) is not int or type(output_words) is not int or not 1<=input_words<=MAX_INPUT_WORDS or not 1<=output_words<=MAX_OUTPUT_WORDS or output_words>524288 and output_words not in (655360,786432):raise ValueError('Invalid portable word strides')
    batches=list(batches)
    if not batches:raise ValueError('Empty portable dispatch sequence')
    counts=[]
    for packed in batches:
        if len(packed)<4:raise ValueError('Missing portable batch header')
        count,=struct.unpack_from('<I',packed)
        if not 1<=count<=65536 or 1+count*input_words>0xffffffff or count*output_words>0xffffffff or len(packed)!=(1+count*input_words)*4:raise ValueError('Invalid portable wire dimensions')
        counts.append(count)
    outputs,hashes=build(source,entry)
    resident=resident_plan(source,entry,outputs)
    if backend=='cuda':
        raw,transports=execute_cuda_batches(outputs['cuda'],entry,batches,[n*output_words*4 for n in counts],counts,**({'resident':resident} if resident else {}))
    else:
        if platform.system()!='Darwin':raise RuntimeError('Metal requires macOS')
        with tempfile.TemporaryDirectory(prefix='sequence-',dir=ROOT/'research/portable-build') as tmp:
            paths=[]
            for i,packed in enumerate(batches):
                inp,out=Path(tmp)/f'{i}.in',Path(tmp)/f'{i}.out';inp.write_bytes(packed)
                paths.append(dict(input=str(inp),output=str(out)))
            manifest=Path(tmp)/'batches.json';manifest.write_text(json.dumps(paths))
            process=run_metal_command(['swift',str(ROOT/'scripts/run-metal-probe.swift'),str(outputs['metal']),str(manifest),'--batches',entry,str(input_words),str(output_words),*([str(resident['stride'])] if resident else [])])
            if process.returncode:raise RuntimeError(process.stderr or process.stdout)
            status=json.loads(process.stdout);transports=status['batches'];raw=[Path(p['output']).read_bytes() for p in paths]
            for t in transports:t.update(compile_timeout_seconds=300,gpu_timeout_seconds=120)
    if len(raw)!=len(batches) or len(transports)!=len(batches) or hashes!=source_hashes(source):raise RuntimeError('Incomplete GPU dispatch sequence or source changed')
    generated={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in outputs.items()}
    results=[]
    for i,(packed,output,transport,count) in enumerate(zip(batches,raw,transports,counts)):
        if len(output)!=count*output_words*4 or transport['cases']!=count or transport['command_status']!='completed':raise RuntimeError('Invalid GPU output stride or transport')
        transport.update(session_dispatches=len(batches),session_dispatch_index=i,pipeline_instances=1,buffer_allocations=3 if resident else 2)
        results.append((output,dict(**(dict(resident_runtime=resident) if resident else {}),transport=transport,source_sha256=hashes,generated_sha256=generated,input_sha256=hashlib.sha256(packed).hexdigest(),output_sha256=hashlib.sha256(output).hexdigest(),gpu_execution_verified=True,backend=backend)))
    return results



@contextlib.contextmanager
def _cuda_module(artifact_bytes,entry,artifact_kind,resident,*,jit_opt_level=None):
    """Shared driver/context/module lifecycle, with no battle allocations."""
    if jit_opt_level is not None and (type(jit_opt_level) is not int or jit_opt_level not in range(5) or artifact_kind!='ptx'):
        raise ValueError('Driver JIT optimization requires PTX and integer0..4')
    artifact_buffer=C.create_string_buffer(artifact_bytes)
    driver=C.WinDLL('nvcuda.dll')
    signatures=dict(cuInit=[C.c_uint],cuDeviceGet=[C.POINTER(C.c_int),C.c_int],cuDeviceGetName=[C.c_char_p,C.c_int,C.c_int],
        cuDeviceComputeCapability=[C.POINTER(C.c_int),C.POINTER(C.c_int),C.c_int],
        cuCtxCreate_v2=[C.POINTER(C.c_void_p),C.c_uint,C.c_int],cuCtxDestroy_v2=[C.c_void_p],
        cuModuleLoadData=[C.POINTER(C.c_void_p),C.c_void_p],cuModuleGetFunction=[C.POINTER(C.c_void_p),C.c_void_p,C.c_char_p],
        cuModuleGetGlobal_v2=[C.POINTER(C.c_uint64),C.POINTER(C.c_size_t),C.c_void_p,C.c_char_p],
        cuMemAlloc_v2=[C.POINTER(C.c_uint64),C.c_size_t],cuMemcpyHtoD_v2=[C.c_uint64,C.c_void_p,C.c_size_t],
        cuMemcpyDtoH_v2=[C.c_void_p,C.c_uint64,C.c_size_t],cuCtxSynchronize=[],
        cuLaunchKernel=[C.c_void_p,*([C.c_uint]*7),C.c_void_p,C.c_void_p,C.c_void_p])
    for name, signature in signatures.items():
        getattr(driver,name).argtypes=signature;getattr(driver,name).restype=C.c_int
    if jit_opt_level is not None:
        driver.cuModuleLoadDataEx.argtypes=[C.POINTER(C.c_void_p),C.c_void_p,C.c_uint,C.POINTER(C.c_int),C.POINTER(C.c_void_p)]
        driver.cuModuleLoadDataEx.restype=C.c_int
    def call(name,*args):
        code=getattr(driver,name)(*args)
        if code:raise RuntimeError(f'{name}: CUDA error {code}')
    context=C.c_void_p()
    call('cuInit',0);device=C.c_int();call('cuDeviceGet',C.byref(device),0)
    if artifact_kind=='cubin':
        major=C.c_int();minor=C.c_int();call('cuDeviceComputeCapability',C.byref(major),C.byref(minor),device)
        if (major.value,minor.value)!=(8,6):raise RuntimeError('The native CUDA artifact requires SM86')
    name=C.create_string_buffer(256);call('cuDeviceGetName',name,256,device)
    try:
        call('cuCtxCreate_v2',C.byref(context),0,device)
        module=C.c_void_p();function=C.c_void_p()
        if jit_opt_level is None:
            call('cuModuleLoadData',C.byref(module),C.cast(artifact_buffer,C.c_void_p))
        else:
            # CU_JIT_OPTIMIZATION_LEVEL=7; scalar option values are cast to void*, not pointers to scalars.
            options=(C.c_int*1)(7);values=(C.c_void_p*1)(jit_opt_level)
            call('cuModuleLoadDataEx',C.byref(module),C.cast(artifact_buffer,C.c_void_p),1,options,values)
        call('cuModuleGetFunction',C.byref(function),module,entry.encode())
        global_ptr=C.c_uint64();global_size=C.c_size_t()
        call('cuModuleGetGlobal_v2',C.byref(global_ptr),C.byref(global_size),module,b'SLANG_globalParams')
        if global_size.value!=(48 if resident else 32):raise RuntimeError('Unexpected Slang CUDA constant buffer ABI')
        yield call,function,global_ptr,dict(backend="cuda",device=name.value.decode(),constant_buffer_bytes=global_size.value)
    finally:
        if context:
            primary = sys.exc_info()[1]
            try:call('cuCtxDestroy_v2',context)
            except Exception as cleanup_error:
                if primary is None:raise
                primary.add_note('CUDA context cleanup also failed: '+str(cleanup_error))


def execute_cuda(source, entry, packed, output_size, count,*,resident=None):
    raw,transports=execute_cuda_batches(source,entry,[packed],[output_size],[count],**({'resident':resident} if resident else {}))
    return raw[0],transports[0]


def compile_cuda_source(source, *, artifact_kind=None):
    """CPU-only compiler/cache path; never loads nvcuda or creates a context."""
    if os.name != 'nt':raise RuntimeError('CUDA compiler requires Windows')
    artifact_kind=cuda_artifact_kind() if artifact_kind is None else artifact_kind
    cuda_bin = Path(os.environ.get('CUDA_PATH', r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.3'))/'bin'
    compiler_files=sorted(cuda_bin.glob('nvrtc*.dll'))
    libraries=[p for p in compiler_files if p.name.lower().startswith('nvrtc64_')]
    builtins=[p for p in compiler_files if p.name.lower().startswith('nvrtc-builtins64_')]
    if len(libraries)!=1 or len(builtins)!=1:
        raise RuntimeError('CUDA compiler root requires exactly one NVRTC and one builtins DLL')
    with os.add_dll_directory(str(cuda_bin)):
        def load_compiler():
            lib = C.WinDLL(str(libraries[0]))
            # NVRTC's internal bare-name LoadLibrary need not use Python's
            # AddDllDirectory search context. Load the fingerprinted companion
            # explicitly, and retain it for the entire compilation lifetime.
            # This factory is never invoked for cache hits or required misses.
            lib._nikke_builtins = C.WinDLL(str(builtins[0]))
            signatures = dict(nvrtcCreateProgram=[C.POINTER(C.c_void_p),C.c_char_p,C.c_char_p,C.c_int,C.c_void_p,C.c_void_p],
                          nvrtcCompileProgram=[C.c_void_p,C.c_int,C.POINTER(C.c_char_p)],
                          nvrtcGetProgramLogSize=[C.c_void_p,C.POINTER(C.c_size_t)], nvrtcGetPTXSize=[C.c_void_p,C.POINTER(C.c_size_t)],
                          nvrtcGetProgramLog=[C.c_void_p,C.c_void_p], nvrtcGetPTX=[C.c_void_p,C.c_void_p],
                          nvrtcDestroyProgram=[C.POINTER(C.c_void_p)])
            if artifact_kind=='cubin':
                signatures.update(nvrtcGetCUBINSize=[C.c_void_p,C.POINTER(C.c_size_t)],nvrtcGetCUBIN=[C.c_void_p,C.c_void_p])
            for name, signature in signatures.items():
                getattr(lib,name).argtypes=signature; getattr(lib,name).restype=C.c_int
            return lib
        # Exact-byte cache validation precedes DLL loading. Hits and required
        # misses need file reads only, without activating NVRTC at all.
        artifact_bytes,compile_receipt=compile_cuda_artifact(None,source.read_bytes(),compiler_files,artifact_kind=artifact_kind,library_factory=load_compiler)
        # Capture exact compiled bytes for independent local audits, including hits.
        source.with_suffix('.'+artifact_kind).write_bytes(artifact_bytes)
    return artifact_bytes,compile_receipt


def execute_cuda_batches(source, entry, batches, output_sizes, counts,*,resident=None):
    """Opt-in sequential dispatches sharing one NVRTC build and CUDA context.
    The pinned Slang StructuredBuffer ABI is pointer + size_t; validate the
    actual constant-symbol size before copying. No numeric/game logic here.
    """
    if not batches or len(batches)!=len(output_sizes) or len(batches)!=len(counts):raise ValueError('Invalid CUDA dispatch sequence')
    for packed,size,count in zip(batches,output_sizes,counts):
        if type(count) is not int or not 1<=count<=65536 or type(size) is not int or size<=0 or len(packed)<4 or struct.unpack_from('<I',packed)[0]!=count:raise ValueError('Invalid CUDA dispatch dimensions')
    if os.name != 'nt':
        raise RuntimeError('This CUDA NVRTC adapter currently requires Windows')
    if resident:
        from portable_resident_layout import verify_cuda_layout_assertions
        verify_cuda_layout_assertions(source,resident)
    artifact_kind=cuda_artifact_kind()
    artifact_bytes,compile_receipt=compile_cuda_source(source,artifact_kind=artifact_kind)
    with _cuda_module(artifact_bytes,entry,artifact_kind,resident) as loaded:
        call,function,global_ptr,module_metadata=loaded
        inp=C.c_uint64();out=C.c_uint64()
        call('cuMemAlloc_v2',C.byref(inp),max(map(len,batches)));call('cuMemAlloc_v2',C.byref(out),max(output_sizes))
        scratch=C.c_uint64();scratch_bytes=resident['stride']*max(counts) if resident else 0
        if resident:call('cuMemAlloc_v2',C.byref(scratch),scratch_bytes)
        results=[];transports=[]
        for packed,output_size,count in zip(batches,output_sizes,counts):
            call('cuMemcpyHtoD_v2',inp,C.cast(C.c_char_p(packed),C.c_void_p),len(packed))
            zero=C.create_string_buffer(output_size);call('cuMemcpyHtoD_v2',out,C.cast(zero,C.c_void_p),output_size)
            params=struct.pack('<'+'Q'*(6 if resident else 4),inp.value,len(packed)//4,out.value,output_size//4,*([scratch.value,max(counts)] if resident else []))
            call('cuMemcpyHtoD_v2',global_ptr,C.cast(C.c_char_p(params),C.c_void_p),len(params))
            started=time.perf_counter();call('cuLaunchKernel',function,count,1,1,1,1,1,0,None,None,None);call('cuCtxSynchronize')
            elapsed=time.perf_counter()-started
            output=C.create_string_buffer(output_size);call('cuMemcpyDtoH_v2',output,out,output_size)
            results.append(output.raw);transports.append(dict(backend='cuda',device=module_metadata['device'],cases=count,command_status='completed',host_dispatch_seconds=elapsed,compile_artifact=compile_receipt))
        if resident:
            for transport in transports:transport.update(runtime_stride_bytes=resident['stride'],runtime_buffer_bytes=scratch_bytes,runtime_element_capacity=max(counts))
        return results,transports


def inspect_cuda_module(source,entry,*,resident=None,jit_opt_level=None):
    """Load/JIT an exact cached PTX; never allocate, copy, sync or launch."""
    if os.name!='nt':raise RuntimeError('CUDA module check requires Windows')
    if os.environ.get('NIKKE_CUDA_CACHE_REQUIRED')!='1' or cuda_artifact_kind()!='ptx':
        raise ValueError('CUDA module check requires cache-only PTX')
    if resident:
        from portable_resident_layout import verify_cuda_layout_assertions
        verify_cuda_layout_assertions(source,resident)
    artifact,receipt=compile_cuda_source(source,artifact_kind='ptx')
    if receipt.get('enabled') is not True or receipt.get('hit') is not True or receipt.get('identity',{}).get('artifact')!='ptx':
        raise ValueError('CUDA module check did not obtain a verified PTX cache hit')
    with _cuda_module(artifact,entry,'ptx',resident,jit_opt_level=jit_opt_level) as loaded:
        metadata=dict(loaded[3],module_verified=True,artifact_kind='ptx',compile_artifact=receipt,
                      kernel_calls=0,buffer_allocations=0,calculation_verified=False,jit_optimization_level=jit_opt_level)
    return metadata

def cuda_artifact_kind():
    kind=os.environ.get('NIKKE_CUDA_ARTIFACT','cubin')
    if kind not in ('ptx','cubin'):raise ValueError('NIKKE_CUDA_ARTIFACT must be cubin or ptx')
    return kind


def cuda_compile_options(kind, ptxas_level=None):
    if kind not in ('ptx','cubin'):raise ValueError('Invalid CUDA artifact kind')
    if ptxas_level is not None and (kind!='cubin' or type(ptxas_level) is not int or ptxas_level not in range(4)):
        raise ValueError('ptxas optimization level requires CUBIN and integer0..3')
    options=['--std=c++17','--gpu-architecture='+('sm_86' if kind=='cubin' else 'compute_86'),'--fmad=false']
    # NVRTC11.3 accepts the forwarding option and payload as separate argv
    # strings. Its parser rejects the joined '= -O' form before compilation.
    if ptxas_level is not None:options.extend(['--ptxas-options','-O'+str(ptxas_level)])
    return options


def compile_cuda_artifact(lib, source, compiler_files, *, artifact_kind=None, library_factory=None):
    from portable_compile_cache import get_or_compile,quoted_headers
    artifact_kind=cuda_artifact_kind() if artifact_kind is None else artifact_kind
    level=os.environ.get('NIKKE_CUDA_PTXAS_OPT_LEVEL')
    if level not in (None,'','0','1','2','3'):raise ValueError('Invalid NIKKE_CUDA_PTXAS_OPT_LEVEL')
    options = cuda_compile_options(artifact_kind,None if level in (None,'') else int(level))
    required=os.environ.get('NIKKE_CUDA_CACHE_REQUIRED','0')
    if required not in ('0','1'):raise ValueError('NIKKE_CUDA_CACHE_REQUIRED must be0 or1')
    directory=os.environ.get('NIKKE_CUDA_COMPILE_CACHE') or None
    if required=='1' and directory is None:raise ValueError('Required CUDA cache directory is missing')
    def compile_now():
        nonlocal lib
        if required=='1':raise RuntimeError('Cold CUDA compilation forbidden; required cache miss')
        if lib is None:lib=library_factory()
        def check(code):
            if code: raise RuntimeError(f'NVRTC error {code}')
        program=C.c_void_p()
        try:
            check(lib.nvrtcCreateProgram(C.byref(program),source,b'portable.cu',0,None,None))
            encoded=[option.encode() for option in options]
            code=lib.nvrtcCompileProgram(program,len(encoded),(C.c_char_p*len(encoded))(*encoded))
            size=C.c_size_t();check(lib.nvrtcGetProgramLogSize(program,C.byref(size)))
            log=C.create_string_buffer(size.value);check(lib.nvrtcGetProgramLog(program,log))
            if code: raise RuntimeError(log.value.decode('utf-8','replace'))
            get_size=getattr(lib,'nvrtcGetCUBINSize' if artifact_kind=='cubin' else 'nvrtcGetPTXSize')
            get_data=getattr(lib,'nvrtcGetCUBIN' if artifact_kind=='cubin' else 'nvrtcGetPTX')
            check(get_size(program,C.byref(size)))
            if size.value==0:raise RuntimeError('NVRTC returned an empty '+artifact_kind+' artifact')
            artifact=C.create_string_buffer(size.value);check(get_data(program,artifact))
            if artifact_kind=='cubin' and not artifact.raw.startswith(b'\x7fELF'):
                raise RuntimeError('NVRTC CUBIN artifact is not a native ELF binary')
            return artifact.raw
        finally:
            if program: lib.nvrtcDestroyProgram(C.byref(program))
    artifact,receipt=get_or_compile(source,options,compiler_files,compile_now,directory,header_files=quoted_headers(source),artifact_kind=artifact_kind)
    if artifact_kind=='cubin' and not artifact.startswith(b'\x7fELF'):
        raise RuntimeError('NVRTC CUBIN artifact is not a native ELF binary')
    return artifact,receipt
