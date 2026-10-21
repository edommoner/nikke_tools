"""Lexical generated-CUDA measurements; never compile, load or execute code."""
import hashlib
import re

_NON_CODE=re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',re.S)
_FUNCTION=re.compile(r'(?m)^[^\n{};]*\b([A-Za-z_]\w*)\s*\([^{};]*\)\s*\{')


def cuda_statistics(raw,*,top=12):
    if type(top) is not int or not 1<=top<=50:raise ValueError('Function count must be1..50')
    source=raw.decode('utf-8')
    def mask(match):return ''.join('\n' if c=='\n' else ' ' for c in match.group())
    code=_NON_CODE.sub(mask,source);functions=[]
    for match in _FUNCTION.finditer(code):
        name=match.group(1)
        if name in ('if','for','while','switch','catch'):continue
        end=match.end();depth=1
        while depth and end<len(code):
            depth+=(code[end]=='{')-(code[end]=='}');end+=1
        if depth:raise ValueError('Unbalanced generated function: '+name)
        body=code[match.end():end]
        functions.append(dict(name=name,line=source.count('\n',0,match.start())+1,
                              bytes=len(source[match.start():end].encode('utf-8')),
                              lines=body.count('\n')+1,noinline='__noinline__' in match.group(),
                              global_entry='__global__' in match.group(),
                              branches=len(re.findall(r'\b(?:if|for|while|switch)\s*\(',body))))
    return dict(schema=1,source_bytes=len(raw),source_sha256=hashlib.sha256(raw).hexdigest(),
                functions=len(functions),noinline_functions=sum(f['noinline'] for f in functions),
                largest_functions=sorted(functions,key=lambda f:(-f['bytes'],f['line']))[:top],
                scope='Lexical generated-CUDA spans only; not compiler time, memory attribution, performance or correctness proof')
