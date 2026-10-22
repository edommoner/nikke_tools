"""Explicit focus-object diagnostic; never a CUBIN cache or calculation proof."""
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


def validate_object(raw):
    # ELF64 little-endian ET_REL / EM_CUDA. This rejects linked executables and
    # truncated sections; it does not prove relocation or ABI link correctness.
    if len(raw)<64 or raw[:7]!=b'\x7fELF\x02\x01\x01':raise ValueError('Expected ELF64 little-endian relocatable CUDA object')
    kind,machine,version=struct.unpack_from('<HHI',raw,16)
    shoff=struct.unpack_from('<Q',raw,40)[0]
    ehsize,phentsize,phnum,shentsize,shnum,shstrndx=struct.unpack_from('<HHHHHH',raw,52)
    if (kind,machine,version,ehsize,phnum,shentsize)!=(1,190,1,64,0,64) or not shnum or not 0<shstrndx<shnum or shoff<64 or shoff+64*shnum>len(raw):
        raise ValueError('Invalid relocatable CUDA ELF header or section table')
    for index in range(shnum):
        section=struct.unpack_from('<IIQQQQIIQQ',raw,shoff+index*64)
        typ=section[1];offset,size=section[4:6]
        if typ!=8 and (offset>len(raw) or size>len(raw)-offset):raise ValueError('Truncated CUDA ELF section')
    return dict(format='elf64-little',type='relocatable',machine='cuda',sections=shnum,bytes=len(raw),sha256=assembler.digest(raw))


def identity(tool,source):
    return dict(schema=1,provider='diagnostic-partition-ptxas',artifact='diagnostic-relocatable-object',
        tool=tool,options=OPTIONS,origin=source)


def run(capture,tool,raw,source,*,journal,popen=None,inspector=None):
    capture=Path(capture).resolve();tool=Path(tool).resolve();tool_info=assembler.validate_tool(tool)
    if assembler.validate_ptx(raw)!=source['input']:raise ValueError('Focus input changed')
    input_path=capture/'focus.ptx';partial=capture/'focus.o.partial';output=capture/'focus.o'
    if partial.exists() or output.exists():raise FileExistsError('Focus object already exists')
    with input_path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    journal.emit('partition_object_tool','verified',tool=tool_info)
    journal.emit('partition_object_input','verified',input=source['input'])
    argv=[str(tool),*OPTIONS,str(input_path),'-o',str(partial)]
    journal.emit('partition_object_ptxas','entered',argv=argv,tool_sha256=tool_info['sha256'])
    creator=popen or subprocess.Popen;reader=inspector or assembler.inspect_process
    started=time.perf_counter();process=None
    try:
        with (capture/'assembler.stdout.log').open('xb') as stdout,(capture/'assembler.stderr.log').open('xb') as stderr:
            process=creator(argv,cwd=capture,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,shell=False,
                creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name=='nt' else 0)
            snapshot=reader(process)
            if not assembler.contained(snapshot,os.getpid(),process.pid):raise RuntimeError('Focus assembler is not in the validation Job')
            journal.emit('partition_object_child','verified',inspection=snapshot)
            code=process.wait(timeout=55)
        elapsed=time.perf_counter()-started
        journal.emit('partition_object_ptxas','returned',return_code=code,elapsed_seconds=elapsed)
        if code:raise RuntimeError('Focus ptxas failed with exit code '+str(code))
        if assembler.validate_tool(tool)!=tool_info or input_path.read_bytes()!=raw:raise ValueError('Focus tool/input changed during execution')
        artifact=validate_object(partial.read_bytes())
        with partial.open('r+b') as stream:os.fsync(stream.fileno())
        if output.exists():raise FileExistsError('Focus object already exists')
        partial.rename(output)
        proof=identity(tool_info,source)
        receipt=dict(identity=proof,key=assembler.digest(json.dumps(proof,sort_keys=True,separators=(',',':')).encode()),artifact=artifact,elapsed_seconds=elapsed)
        journal.emit('partition_object_receipt','verified',receipt=receipt)
        return receipt
    except BaseException as error:
        journal.emit('partition_object_failure','raised',exception=type(error).__name__)
        if process is not None and process.poll() is None:process.terminate();process.wait(timeout=5)
        raise
