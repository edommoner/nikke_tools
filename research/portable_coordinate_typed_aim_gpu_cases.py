"""All positive CPU aim fixtures plus the real last typed slot, with originals."""
import copy
from portable_coordinate_typed_aim_cases import fixtures as reference_cases

def fixtures():
    rows=[r for r in reference_cases() if not r.get('expect_reference_gap')]
    c=copy.deepcopy(rows[3]);c['name']='coordinate-typed-aim/manual-last-slot';c['body']['duration']=1
    c['patterns'][0]['until']['time']=2;c['body']['enemy']['patterns']=copy.deepcopy(c['patterns'])
    front,back=c['typed_bindings'];a,b=c['typed_geometry']['shapes']
    c['typed_bindings']=[front]+[dict(node=front['node'],kind=2,identity=10+i,capacity=1e30,label='typed-reserve-'+str(i)) for i in range(1,127)]+[dict(back,identity=137)]
    c['typed_geometry']['shapes']=[a]+[dict(x=1e7,y=0.,r=1.,z=-1.) for _ in range(126)]+[b]
    rows.append(c);return rows
