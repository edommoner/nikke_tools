"""Pinned device linker and static linked-CUDA-ELF checks; no driver API."""
import struct
from pathlib import Path
from portable_offline_assembler import digest

TOOL_VERSION='12.4.131'
TOOL_SHA256='60d8c8bca6df7d7ec2aafef688192f46bb7d76bd94c4f82f5a520ff278ea5ceb'
ARCHIVE_SHA256='3b14cf8dd9dda4a3b1a9682270d46eef775f018e17650187a8a448a06111f2b8'
OPTIONS=['-arch=sm_86','--ignore-host-info','--verbose']


def validate_tool(path):
    raw=Path(path).read_bytes()
    if digest(raw)!=TOOL_SHA256 or not raw.startswith(b'MZ'):raise ValueError('Device linker is not the pinned NVIDIA component')
    return dict(version=TOOL_VERSION,sha256=TOOL_SHA256,archive_sha256=ARCHIVE_SHA256,bytes=len(raw))


def validate_cubin(raw):
    if len(raw)<64 or raw[:7]!=b'\x7fELF\x02\x01\x01':raise ValueError('Expected ELF64 little-endian CUDA executable')
    kind,machine,version=struct.unpack_from('<HHI',raw,16)
    phoff,shoff=struct.unpack_from('<QQ',raw,32);flags=struct.unpack_from('<I',raw,48)[0]
    ehsize,phentsize,phnum,shentsize,shnum,shstrndx=struct.unpack_from('<HHHHHH',raw,52)
    if (kind,machine,ehsize,shentsize)!=(2,190,64,64) or version==0 or not shnum or not 0<shstrndx<shnum or shoff<64 or shoff+64*shnum>len(raw):raise ValueError('Invalid linked CUDA ELF header/table')
    if flags&0xff!=86 or not flags&0x400:raise ValueError('Linked CUDA image must target sm_86 with 64-bit addresses')
    if phnum:
        if phentsize!=56 or phoff<64 or phoff+56*phnum>len(raw):raise ValueError('Invalid CUDA program header table')
        for index in range(phnum):
            typ,_,offset,_,_,filesz,memsz,_=struct.unpack_from('<IIQQQQQQ',raw,phoff+index*56)
            if offset>len(raw) or filesz>len(raw)-offset or (typ==1 and memsz<filesz):raise ValueError('Truncated CUDA program segment')
    sections=[struct.unpack_from('<IIQQQQIIQQ',raw,shoff+i*64) for i in range(shnum)]
    for row in sections:
        if row[1]!=8 and (row[4]>len(raw) or row[5]>len(raw)-row[4]):raise ValueError('Truncated linked CUDA section')
    def string(table,index):
        if table[1]!=3 or index>=table[5]:raise ValueError('Invalid CUDA string table reference')
        start=table[4]+index;end=raw.find(b'\0',start,table[4]+table[5])
        if end<0:raise ValueError('Unterminated CUDA symbol string')
        return raw[start:end]
    names=sections[shstrndx]
    for section in sections:string(names,section[0])
    wanted={b'portableEvents':[],b'SLANG_globalParams':[]}
    for table in sections:
        if table[1] not in (2,11):continue
        if table[9]!=24 or table[5]%24 or not 0<table[6]<shnum:raise ValueError('Invalid CUDA symbol table')
        strings=sections[table[6]]
        for at in range(table[4],table[4]+table[5],24):
            name,info,other,index,value,size=struct.unpack_from('<IBBHQQ',raw,at);symbol=string(strings,name)
            if symbol in wanted:wanted[symbol].append(dict(info=info,other=other,section=index,value=value,bytes=size))
    if any(len(rows)!=1 for rows in wanted.values()):raise ValueError('Unique kernel and parameter symbols required')
    kernel=wanted[b'portableEvents'][0];parameters=wanted[b'SLANG_globalParams'][0]
    for symbol in (kernel,parameters):
        if not 0<symbol['section']<shnum or symbol['bytes']<=0:raise ValueError('Undefined or empty CUDA binding symbol')
    code=sections[kernel['section']]
    if kernel['info']&15!=2 or code[1]!=1 or not code[2]&4 or not code[5]:raise ValueError('CUDA kernel has no executable code section')
    if parameters['bytes']!=48 or sections[parameters['section']][5]<48:raise ValueError('CUDA global parameter size must be48 bytes')
    return dict(format='elf64-little',type='executable',machine='cuda',cuda_format_version=version,target='sm_86',
        sections=shnum,program_headers=phnum,static_bindings=dict(portableEvents=kernel,SLANG_globalParams=parameters),
        bytes=len(raw),sha256=digest(raw))
