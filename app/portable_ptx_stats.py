"""Read saved PTX declarations; never compile, load a driver or execute code.

PTX virtual registers and local declarations are not physical register counts,
compiler memory attribution, or kernel performance measurements. Grammar source:
https://docs.nvidia.com/cuda/parallel-thread-execution/#variable-declarations
Unsupported declarations fail closed instead of returning partial estimates.
"""
import base64
from bisect import bisect_right
import hashlib
import json
import re

_COMMENTS=re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"',re.S)
_FUNCTION=re.compile(r'(?m)^[ \t]*(?:(?:\.visible|\.weak|\.extern)\s+)*\.(func|entry)\b')
_SYMBOL=r'[%A-Za-z_$][A-Za-z0-9_$]*'
_TYPE=r'(?:pred|[busf](?:8|16|32|64|128))'
_NAME=re.compile(r'\s*('+_SYMBOL+r')')


def _close(code,start,opening,closing):
    depth=0
    for i in range(start,len(code)):
        if code[i]==opening:depth+=1
        elif code[i]==closing:
            depth-=1
            if depth==0:return i+1
    raise ValueError('Unbalanced PTX '+opening)


def _declarations(body):
    body=re.sub(r'\.callprototype\b[^;]*;','',body)
    registers={};local_bytes=0
    for match in re.finditer(r'(?<![\w.])\.(reg|local)\s+([^;]+);',body):
        space,decl=match.groups()
        parsed=re.fullmatch(r'(?:(?:\.align\s+[1-9][0-9]*)\s+)?(?:\.(v[24])\s+)?\.('+_TYPE+r')\s+(.+)',decl.strip(),re.S)
        if parsed is None:raise ValueError('Unsupported PTX '+space+' declaration')
        vector,typ,elements=parsed.groups();width=int(vector[1:]) if vector else 1
        for element in elements.split(','):
            if space=='reg':
                item=re.fullmatch(r'('+_SYMBOL+r')(?:\s*<\s*([1-9][0-9]*)\s*>)?',element.strip())
                if item is None:raise ValueError('Unsupported PTX register element')
                registers[typ]=registers.get(typ,0)+width*int(item.group(2) or 1)
            else:
                item=re.fullmatch(_SYMBOL+r'((?:\s*\[\s*[1-9][0-9]*\s*\])*)',element.strip())
                if item is None or typ=='pred':raise ValueError('Unsupported PTX local element')
                count=width
                for dimension in re.findall(r'[0-9]+',item.group(1)):count*=int(dimension)
                local_bytes+=count*int(typ[1:])//8
    return registers,local_bytes


def ptx_statistics(raw,*,top=8):
    if type(top) is not int or not 1<=top<=50:raise ValueError('Function count must be1..50')
    source=raw.decode('utf-8').rstrip('\0')
    code=_COMMENTS.sub(lambda m:''.join('\n' if c=='\n' else ' ' for c in m.group()),source)
    rows=[];covered=0;newlines=[m.start() for m in re.finditer('\n',code)]
    for match in _FUNCTION.finditer(code):
        if match.start()<covered:continue
        pos=match.end()
        while pos<len(code) and code[pos].isspace():pos+=1
        if pos<len(code) and code[pos]=='(':pos=_close(code,pos,'(',')')
        name=_NAME.match(code,pos)
        if name is None:raise ValueError('Unsupported PTX function symbol')
        pos=name.end()
        # Header parameter lists may have .reg declarations; do not count them
        # as body allocations or mistake a prototype for a function body.
        while pos<len(code):
            c=code[pos]
            if c=='(':pos=_close(code,pos,'(',')');continue
            if c in ';{':break
            pos+=1
        if pos==len(code):raise ValueError('Unterminated PTX function header')
        if code[pos]==';':continue
        end=_close(code,pos,'{','}');covered=end
        registers,local_bytes=_declarations(code[pos+1:end-1])
        rows.append(dict(name=name.group(1),kind=match.group(1),
                         line=bisect_right(newlines,match.start())+1,
                         lines=code[pos:end].count('\n')+1,
                         virtual_registers=registers,
                         virtual_register_count=sum(registers.values()),
                         declared_local_bytes=local_bytes))
    if not rows:raise ValueError('No PTX function definitions found')
    return dict(schema=1,ptx_bytes=len(raw),ptx_sha256=hashlib.sha256(raw).hexdigest(),functions=len(rows),
                largest_functions=sorted(rows,key=lambda r:(-r['declared_local_bytes'],-r['virtual_register_count'],r['line']))[:top],
                scope='PTX virtual declarations only; not physical registers, compiler memory attribution or execution proof')


def saved_ptx_statistics(cache_entry,phases,*,top=8):
    """Anchor cached bytes to an existing verified compile receipt, read only."""
    value=json.loads(cache_entry.read_bytes());identity=value['identity']
    key=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if identity.get('artifact')!='ptx' or cache_entry.name!=key+'.json':raise ValueError('PTX cache identity mismatch')
    raw=base64.b64decode(value['artifact_base64'],validate=True)
    sha=hashlib.sha256(raw).hexdigest()
    if value['artifact_bytes']!=len(raw) or value['artifact_sha256']!=sha:raise ValueError('PTX cache bytes corrupt')
    receipts=[r['receipt'] for r in (json.loads(line) for line in phases.read_text().splitlines())
              if r.get('stage')=='cuda_compile_cache' and r.get('state')=='verified']
    if not any(r.get('key')==key and r.get('identity')==identity and r.get('artifact_sha256')==sha and r.get('artifact_bytes')==len(raw) for r in receipts):
        raise ValueError('Saved PTX compile receipt mismatch')
    result=ptx_statistics(raw,top=top)
    result.update(receipt_match=True,source_integrity_verified=True,analysis_complete=True,
                  compiler_verified=False,calculation_verified=False,nvrtc_compile_calls=0,gpu_calls=0)
    return result
