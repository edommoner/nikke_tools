"""Explicit relocatable-object diagnostics; never a CUBIN cache or calculation proof."""
import json,os,struct,subprocess,time
from pathlib import Path
import portable_offline_assembler as assembler
from portable_ptx_partition import audit_partition

OPTIONS=[*assembler.OPTIONS,'--compile-only']


def origin(cache_entry,phases,candidate,producer):
    candidate=Path(candidate)
    audit=audit_partition(Path(cache_entry),Path(phases),candidate)
    if audit['input_sha256']!=producer['ptx']['sha256'] or audit['cache_key']!=producer['cache_key']:
        raise ValueError('Partition does not belong to the audited PTX producer')
    raw=(candidate/'focus.ptx').read_bytes()
    source=assembler.validate_ptx(raw)
    return dict(schema=1,purpose='diagnostic-focus-relocatable-object',producer=producer,
        partition_plan_sha256=assembler.digest((candidate/'plan.json').read_bytes()),
        focus=audit['focus'],input=source,partition_cpu_audit_verified=True),raw


def module_origin(cache_entry,phases,producer,producer_raw):
    from portable_ptx_stats import load_saved_ptx
    raw,key=load_saved_ptx(Path(cache_entry),Path(phases))
    source=assembler.validate_ptx(raw)
    if raw!=producer_raw or source!=producer['ptx'] or key!=producer['cache_key']:
        raise ValueError('Module PTX/cache differs from the audited original producer')
    return dict(schema=1,purpose='diagnostic-module-relocatable-object',producer=producer,
        input=source,source_bytes_unchanged=True,source_partitioned=False),raw


def object_profile(source):
    purpose=source.get('purpose')
    if purpose=='diagnostic-focus-relocatable-object':
        return dict(stem='focus',provider='diagnostic-partition-ptxas',artifact='diagnostic-relocatable-object',prefix='partition_object',proof='object.json',log='assembler')
    if purpose=='diagnostic-module-relocatable-object':
        return dict(stem='module',provider='diagnostic-module-ptxas',artifact='diagnostic-module-relocatable-object',prefix='partition_object',proof='object.json',log='assembler')
    if purpose=='diagnostic-module-link':
        return dict(stem='linked',provider='diagnostic-nvlink',artifact='diagnostic-linked-cubin',prefix='module_link',proof='link.json',log='linker')
    raise ValueError('Unknown diagnostic object source purpose')


def object_paths(capture,source):
    stem=object_profile(source)['stem'];capture=Path(capture)
    if stem=='linked':return capture/'module.o',capture/'linked.cubin.partial',capture/'linked.cubin'
    return capture/(stem+'.ptx'),capture/(stem+'.o.partial'),capture/(stem+'.o')


def validate_object(raw):
    # ELF64 little-endian ET_REL / EM_CUDA. This rejects linked executables and
    # truncated sections; it does not prove relocation or ABI link correctness.
    if len(raw)<64 or raw[:7]!=b'\x7fELF\x02\x01\x01':raise ValueError('Expected ELF64 little-endian relocatable CUDA object')
    kind,machine,version=struct.unpack_from('<HHI',raw,16)
    shoff=struct.unpack_from('<Q',raw,40)[0]
    ehsize,phentsize,phnum,shentsize,shnum,shstrndx=struct.unpack_from('<HHHHHH',raw,52)
    # EI_VERSION above is generic ELF1; e_version is CUDA's nonzero format
    # version (pinned12.4.131 emitted124). NVIDIA/cuda-rust#622 confirms the
    # distinction. Keep the type/machine/table/payload checks unchanged.
    if version==0 or (kind,machine,ehsize,phnum,shentsize)!=(1,190,64,0,64) or not shnum or not 0<shstrndx<shnum or shoff<64 or shoff+64*shnum>len(raw):
        raise ValueError('Invalid relocatable CUDA ELF header or section table')
    for index in range(shnum):
        section=struct.unpack_from('<IIQQQQIIQQ',raw,shoff+index*64)
        typ=section[1];offset,size=section[4:6]
        if typ!=8 and (offset>len(raw) or size>len(raw)-offset):raise ValueError('Truncated CUDA ELF section')
    return dict(format='elf64-little',type='relocatable',machine='cuda',cuda_format_version=version,sections=shnum,bytes=len(raw),sha256=assembler.digest(raw))


def object_options(source):
    if object_profile(source)['stem']=='linked':
        from portable_device_linker import OPTIONS as link_options
        return link_options
    return OPTIONS


def validate_tool_path(source,path):
    if object_profile(source)['stem']=='linked':
        from portable_device_linker import validate_tool
        return validate_tool(path)
    return assembler.validate_tool(path)


def validate_input(source,raw):
    return validate_object(raw) if object_profile(source)['stem']=='linked' else assembler.validate_ptx(raw)


def validate_output(source,raw):
    if object_profile(source)['stem']=='linked':
        from portable_device_linker import validate_cubin
        return validate_cubin(raw)
    return validate_object(raw)


def identity(tool,source):
    profile=object_profile(source)
    return dict(schema=1,provider=profile['provider'],artifact=profile['artifact'],tool=tool,options=object_options(source),origin=source)


def run(capture,tool,raw,source,*,journal,popen=None,inspector=None):
    capture=Path(capture).resolve();tool=Path(tool).resolve();tool_info=validate_tool_path(source,tool)
    profile=object_profile(source);prefix=profile['prefix']
    if validate_input(source,raw)!=source['input']:raise ValueError('Diagnostic input changed')
    input_path,partial,output=object_paths(capture,source)
    if partial.exists() or output.exists():raise FileExistsError('Diagnostic output already exists')
    with input_path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    journal.emit(prefix+'_tool','verified',tool=tool_info)
    journal.emit(prefix+'_input','verified',input=source['input'])
    argv=[str(tool),*object_options(source),str(input_path),'-o',str(partial)]
    journal.emit(prefix+('_tool_run' if profile['stem']=='linked' else '_ptxas'),'entered',argv=argv,tool_sha256=tool_info['sha256'])
    creator=popen or subprocess.Popen;reader=inspector or assembler.inspect_process
    started=time.perf_counter();process=None
    try:
        with (capture/(profile['log']+'.stdout.log')).open('xb') as stdout,(capture/(profile['log']+'.stderr.log')).open('xb') as stderr:
            process=creator(argv,cwd=capture,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,shell=False,
                creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name=='nt' else 0)
            snapshot=reader(process)
            if not assembler.contained(snapshot,os.getpid(),process.pid):raise RuntimeError('Native tool is not in the validation Job')
            journal.emit(prefix+'_child','verified',inspection=snapshot)
            code=process.wait(timeout=55)
        elapsed=time.perf_counter()-started
        journal.emit(prefix+('_tool_run' if profile['stem']=='linked' else '_ptxas'),'returned',return_code=code,elapsed_seconds=elapsed)
        if code:raise RuntimeError('Native tool failed with exit code '+str(code))
        if validate_tool_path(source,tool)!=tool_info or input_path.read_bytes()!=raw:raise ValueError('Native tool/input changed during execution')
        artifact=validate_output(source,partial.read_bytes())
        with partial.open('r+b') as stream:os.fsync(stream.fileno())
        if output.exists():raise FileExistsError('Diagnostic output already exists')
        partial.rename(output)
        proof=identity(tool_info,source)
        receipt=dict(identity=proof,key=assembler.digest(json.dumps(proof,sort_keys=True,separators=(',',':')).encode()),artifact=artifact,elapsed_seconds=elapsed)
        journal.emit(prefix+'_receipt','verified',receipt=receipt)
        return receipt
    except BaseException as error:
        journal.emit(prefix+'_failure','raised',exception=type(error).__name__)
        if process is not None and process.poll() is None:process.terminate();process.wait(timeout=5)
        raise
