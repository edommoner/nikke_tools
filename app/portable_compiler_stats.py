"""Lexical generated-CUDA measurements; never compile, load or execute code."""
import hashlib
import re
from collections import Counter,defaultdict

_NON_CODE=re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',re.S)
_FUNCTION=re.compile(r'(?m)^[^\n{};]*\b([A-Za-z_]\w*)\s*\([^{};]*\)\s*\{')


def cuda_statistics(raw,*,top=12,caller=None):
    if type(top) is not int or not 1<=top<=50:raise ValueError('Function count must be1..50')
    source=raw.decode('utf-8')
    def mask(match):return ''.join('\n' if c=='\n' else ' ' for c in match.group())
    code=_NON_CODE.sub(mask,source);functions=[];calls=[]
    for match in _FUNCTION.finditer(code):
        name=match.group(1)
        if name in ('if','for','while','switch','catch'):continue
        end=match.end();depth=1
        while depth and end<len(code):
            depth+=(code[end]=='{')-(code[end]=='}');end+=1
        if depth:raise ValueError('Unbalanced generated function: '+name)
        body=code[match.end():end]
        calls.append(Counter(re.findall(r'\b([A-Za-z_]\w*)\s*\(',body)))
        functions.append(dict(name=name,line=source.count('\n',0,match.start())+1,
                              bytes=len(source[match.start():end].encode('utf-8')),
                              lines=body.count('\n')+1,noinline='__noinline__' in match.group(),
                              global_entry='__global__' in match.group(),
                              branches=len(re.findall(r'\b(?:if|for|while|switch)\s*\(',body))))
    result=dict(schema=1,source_bytes=len(raw),source_sha256=hashlib.sha256(raw).hexdigest(),
                functions=len(functions),noinline_functions=sum(f['noinline'] for f in functions),
                largest_functions=sorted(functions,key=lambda f:(-f['bytes'],f['line']))[:top],
                scope='Lexical generated-CUDA spans only; not compiler time, memory attribution, performance or correctness proof')
    if caller is not None:
        if not isinstance(caller,str) or not caller:raise ValueError('Expected a generated caller symbol')
        by_name=defaultdict(list)
        for i,f in enumerate(functions):by_name[f['name']].append(i)
        if len(by_name[caller])!=1:raise ValueError('Caller is absent or ambiguous')
        pending=[(by_name[caller][0],0)];seen=set();edges=[];truncated=False
        while pending:
            i,depth=pending.pop(0)
            if i in seen:continue
            if len(seen)==200:truncated=True;break
            seen.add(i)
            for name,count in sorted(calls[i].items()):
                targets=by_name.get(name,[])
                if not targets:continue
                edge=dict(caller=functions[i]['name'],callee=name,calls=count,depth=depth+1,ambiguous=len(targets)!=1)
                if len(targets)==1:
                    target=targets[0];f=functions[target]
                    edge.update(noinline=f['noinline'],bytes=f['bytes'],lines=f['lines'])
                    if not f['noinline'] and depth<2:pending.append((target,depth+1))
                edges.append(edge)
        result['call_graph']=dict(root=caller,max_depth=3,visited_functions=len(seen),truncated=truncated,edges=edges,
            scope='Known lexical calls; stop at noinline or depth3. No claim about actual compiler inlining or memory cost')
    return result
