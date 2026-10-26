"""Literal typed shapes and point query; no target state or schedule is encoded."""
import struct
from portable_geometry_specs import number
MAGIC=0x54474731
WORDS=2320
ROWS=128
ROW_WORDS=18

def normalize(spec,count,kind):
    if type(count) is not int or not 1<=count<=ROWS or type(kind) is not int or kind not in (2,3):raise ValueError('Bounded typed geometry kind/count required')
    if not isinstance(spec,dict) or set(spec)-{'point','grow','shapes'}:raise ValueError('Unknown typed geometry field')
    point=spec.get('point')
    if not isinstance(point,list) or len(point)!=2:raise ValueError('Explicit typed geometry point required')
    point=[float(number(v)) for v in point];grow=float(number(spec.get('grow',0),nonnegative=True));shapes=spec.get('shapes')
    if not isinstance(shapes,list) or len(shapes)!=count:raise ValueError('One typed shape per binding required')
    rows=[]
    for shape in shapes:
        if not isinstance(shape,dict) or set(shape)-{'x','y','r','w','h','rot','z'} or not {'x','y'}<=set(shape):raise ValueError('Literal typed circle or rectangle required')
        values=[float(number(shape.get(k,0))) for k in ('x','y','r','w','h','rot','z')]
        x,y,r,w,h,rot,z=values
        if r>0 and w==h==0:tag=1
        elif r==0 and w>0 and h>0:tag=2
        else:raise ValueError('Invalid typed shape dimensions')
        rows.append(dict(kind=tag,x=x,y=y,r=r,w=w,h=h,rot=rot,z=z))
    return dict(kind=kind,point=point,grow=grow,shapes=rows)

def pack(spec,count,kind):
    data=normalize(spec,count,kind);words=[0]*WORDS;words[:4]=[MAGIC,1,count,kind]
    def bits(v):return list(struct.unpack('<II',struct.pack('<d',v)))
    words[4:10]=sum((bits(v) for v in [*data['point'],data['grow']]),[])
    for i,row in enumerate(data['shapes']):
        at=16+i*ROW_WORDS;words[at]=row['kind'];words[at+2:at+16]=sum((bits(row[k]) for k in ('x','y','r','w','h','rot','z')),[])
    return words,data
