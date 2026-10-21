"""Fail-closed reflection contract for the optional GPU-owned Runtime buffer."""
import json
from pathlib import Path


def _layout(resource):
    ty=resource['type'];state=ty['resultType']
    if ty.get('kind')!='resource' or ty.get('baseShape')!='structuredBuffer' or ty.get('access')!='readWrite' or state.get('kind')!='struct' or state.get('name')!='Runtime':raise ValueError('Unknown resident Runtime resource')
    sizes=state['sizes']
    if len(sizes)!=1 or sizes[0]['kind']!='uniform':raise ValueError('Unknown resident Runtime size')
    stride=sizes[0]['value'];alignment=sizes[0]['alignment']
    if type(stride) is not int or not 0<stride<=1048576 or alignment!=8 or stride%8:raise ValueError('Invalid resident Runtime stride')
    fields=[];end=0
    for field in state['fields']:
        t=field['type'];binding=field['binding'];count=1
        if t['kind']=='array':count=t['elementCount'];t=t['elementType']
        width={'uint32':4,'int32':4,'uint64':8}.get(t.get('scalarType'))
        if t['kind']!='scalar' or width is None or type(count) is not int or count<=0:raise ValueError('Unknown resident Runtime field')
        offset=binding['offset'];size=binding['size']
        if binding['kind']!='uniform' or offset<end or offset%width or size!=count*width or offset+size>stride:raise ValueError('Invalid resident Runtime field layout')
        fields.append(dict(name=field['name'],scalar=t['scalarType'],count=count,offset=offset,size=size));end=offset+size
    if not fields or (end+7)//8*8!=stride:raise ValueError('Resident Runtime trailing layout changed')
    return dict(stride=stride,alignment=alignment,fields=fields)


def reflection_plan(paths,entry):
    plans={}
    for target,path in paths.items():
        r=json.loads(Path(str(path)+'.reflection.json').read_text())
        if [e['name'] for e in r['entryPoints']]!=[entry]:raise ValueError('Resident reflection entry changed')
        parameters=r['parameters']
        if [p['name'] for p in parameters]!=['commands','results','runtimeStates']:raise ValueError('Resident buffer binding order changed')
        for i,p in enumerate(parameters):
            binding=p['binding']
            if target=='metal':
                if binding!=dict(kind='constantBuffer',index=i):raise ValueError('Resident Metal buffer binding changed')
            elif target=='cuda':
                if binding!=dict(kind='uniform',offset=i*16,size=16,elementStride=0):raise ValueError('Resident CUDA constant ABI changed')
            else:raise ValueError('Unknown resident target')
        for p in parameters[:2]:
            t=p['type']
            if t.get('baseShape')!='structuredBuffer' or t['resultType'].get('scalarType')!='uint32':raise ValueError('Resident input/output word type changed')
        plans[target]=_layout(parameters[2])
    if set(plans)!= {'cuda','metal'} or plans['cuda']!=plans['metal']:raise ValueError('CUDA/Metal Runtime layout differs')
    return dict(schema=1,**plans['cuda'],bindings=dict(commands=0,results=1,runtimeStates=2),cuda_constant_bytes=48)


def cuda_layout_assertions(raw,plan):
    import re
    text=raw.decode()
    names=re.findall(r'(?m)^struct (Runtime_\d+)\s*$',text)
    if len(names)!=1:raise ValueError('Unknown generated CUDA Runtime declaration')
    name=names[0]
    return raw+(f'\n// Transport ABI checks; shared arithmetic and event code above are unmodified.\nstatic_assert(sizeof({name}) == {plan["stride"]}, "Resident Runtime stride mismatch");\nstatic_assert(alignof({name}) == {plan["alignment"]}, "Resident Runtime alignment mismatch");\n').encode()


def verify_cuda_layout_assertions(path,plan):
    raw=Path(path).read_bytes()
    suffix=cuda_layout_assertions(raw,plan)[len(raw):]
    if not raw.endswith(suffix):raise ValueError('Resident CUDA allocation disagrees with compiled layout assertions')
