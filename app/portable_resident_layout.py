"""Fail-closed reflection contract for the optional GPU-owned Runtime buffer."""
import json
import re
from pathlib import Path

def _fields(state,stride,alignment,*,base=0,prefix='',depth=0):
    """Flatten numeric struct leaves without guessing aggregate size/alignment."""
    if depth>8:raise ValueError('Resident Runtime nesting limit exceeded')
    fields=[];end=0;names=set()
    for field in state['fields']:
        name=field['name'];t=field['type'];binding=field['binding'];count=1
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z_]\w*',name) or name in names:raise ValueError('Invalid resident Runtime field name')
        names.add(name);offset=binding['offset'];size=binding['size']
        if type(offset) is not int or type(size) is not int or binding['kind']!='uniform' or offset<end or size<=0 or offset+size>stride:raise ValueError('Invalid resident Runtime field layout')
        if t['kind']=='struct':
            sizes=t['sizes']
            if len(sizes)!=1 or sizes[0]['kind']!='uniform' or sizes[0]['value']!=size or sizes[0]['alignment'] not in (4,8):raise ValueError('Unknown resident Runtime aggregate layout')
            align=sizes[0]['alignment']
            if (base+offset)%align:raise ValueError('Invalid resident Runtime aggregate alignment')
            fields.extend(_fields(t,size,align,base=base+offset,prefix=prefix+name+'.',depth=depth+1))
        else:
            if t['kind']=='array':count=t['elementCount'];t=t['elementType']
            width={'uint32':4,'int32':4,'uint64':8}.get(t.get('scalarType'))
            if t['kind']!='scalar' or width is None or type(count) is not int or count<=0:raise ValueError('Unknown resident Runtime field')
            if (base+offset)%width or size!=count*width:raise ValueError('Invalid resident Runtime field layout')
            fields.append(dict(name=prefix+name,scalar=t['scalarType'],count=count,offset=base+offset,size=size))
        end=offset+size
        if len(fields)>4096:raise ValueError('Resident Runtime leaf limit exceeded')
    if not fields or (end+alignment-1)//alignment*alignment!=stride:raise ValueError('Resident Runtime trailing layout changed')
    return fields


def _layout(resource):
    ty=resource['type'];state=ty['resultType']
    if ty.get('kind')!='resource' or ty.get('baseShape')!='structuredBuffer' or ty.get('access')!='readWrite' or state.get('kind')!='struct' or state.get('name')!='Runtime':raise ValueError('Unknown resident Runtime resource')
    sizes=state['sizes']
    if len(sizes)!=1 or sizes[0]['kind']!='uniform':raise ValueError('Unknown resident Runtime size')
    stride=sizes[0]['value'];alignment=sizes[0]['alignment']
    if type(stride) is not int or not 0<stride<=1048576 or alignment!=8 or stride%8:raise ValueError('Invalid resident Runtime stride')
    fields=_fields(state,stride,alignment)
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
