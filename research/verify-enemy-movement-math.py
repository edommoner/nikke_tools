"""Movement arithmetic/precedence probe; no claim of a GPU world consumer."""
import array,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from enemy_movement_model import integrate
s=importlib.util.spec_from_file_location('movement_math_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
SOURCE='gpu/enemy_movement_math_probe.slang';STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=24,OUTPUT=16)
MAGIC=0x454d4d31
def bits(v):return list(struct.unpack('<II',struct.pack('<d',v)))
def prepare():
    rows=[]
    vectors=[('ordinary',[9.,3.,2.,-.5,0.,0.,1.]),('zero-time',[-0.,0.,1.,-1.,-0.,0.,0.]),
        ('cancellation',[1e16,1.,-1e16,-.5,0.,0.,1.]),('subnormal',[5e-324,-5e-324,5e-324,5e-324,0.,-0.,1.])]
    for label,values in vectors:
        for flags in range(4):
            for precedence in range(2):
                rows.append(('movement-math/'+label+'/'+str(flags)+'/'+str(precedence),[MAGIC,1,flags,precedence,*sum((bits(x) for x in values),[]),*([0]*6)],(flags,precedence,values)))
    for precedence in range(2):
        values=[1e308,0.,1e308,0.,0.,0.,2.]
        rows.append(('movement-math/overflow/'+str(precedence),[MAGIC,1,0,precedence,*sum((bits(x) for x in values),[]),*([0]*6)],(0,precedence,values)))
    seed=rows[0][1]
    for label,index,value in [('magic',0,0),('version',1,2),('flags',2,4),('precedence',3,2),('tail',23,1)]:
        words=list(seed);words[index]=value;rows.append(('reject/movement-math/'+label,words,None))
    for label,index,value in [('negative-time',16,-1.),('nan-position',4,float('nan')),('infinite-speed',8,float('inf')),('nan-center',12,float('nan'))]:
        words=list(seed);words[index:index+2]=bits(value);rows.append(('reject/movement-math/'+label,words,None))
    packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    flags,precedence,v=domain
    try:
        p=integrate(v[:2],v[2:4],v[4:6],v[6],bool(flags&1),bool(flags&2),('disable-before-force','force-before-disable')[precedence])
        return dict(status=0,position_words=sum((bits(x) for x in p),[]),gpu_world_consumer=False)
    except ValueError:return dict(status=16,position_words=[],gpu_world_consumer=False)
def compare(block,domain):
    native=native_reference(domain)
    expected=[native['status']]+[0]*15
    if native['status']==0:expected=[0,MAGIC,domain[0],domain[1],*native['position_words'],*([0]*8)]
    assert list(block)==expected,'Shared ordered movement/precedence binary64 differs'
    return native
def validate_rejection(block,name):assert name.startswith('reject/movement-math/') and list(block)==[64]+[0]*15
