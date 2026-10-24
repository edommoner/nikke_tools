"""Shared policy shape geometry: GPU computes rotation, arcs and break radii."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_coordinate_numeric_v1 as n
from portable_coordinate_geometry_cases import fixtures
s=importlib.util.spec_from_file_location('geometry_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
SOURCE='gpu/coordinate_geometry_probe.slang';INPUT_WORDS=24;OUTPUT_WORDS=4160;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)
def words64(x):return [x&0xffffffff,x>>32]
def pack(values):return [0x43475631,1,values[0],0]+[word for v in values[1:] for word in words64(n.bits(v))]
def prepare():
    n.check_schema(ROOT);entries=[('coordinate-common-geometry/'+name,pack(values),values) for name,values in fixtures()]
    seed=entries[0][1];rect=next(w for _,w,d in entries if d[0]==2)
    for label,base,at,value in [('magic',seed,0,0),('version',seed,1,2),('kind',seed,2,3),('reserved',seed,3,1),('nan',seed,5,0x7ff80000),('radius-zero',seed,9,0),('width-zero',rect,11,0),('radius-negative',seed,9,0xbff00000),('rho-negative',seed,21,0xbff00000),('grow-negative',seed,23,0xbff00000),('dimension-conflict',seed,11,0x3ff00000),('rotation-inf',rect,15,0x7ff00000)]:
        w=list(base);w[at]=value;entries.append(('reject/coordinate-common-geometry/'+label,w,None))
    for label,values in [('overflow-delta',(1,1e308,0.,1.,0.,0.,0.,-1e308,0.,1.,0.)),('overflow-square',(1,1e200,0.,1e200,0.,0.,0.,0.,0.,1e200,0.)),('underflow-denominator',(1,1e-310,0.,1e-310,0.,0.,0.,0.,0.,1e-310,0.))]:
        entries.append(('reject/coordinate-common-geometry/'+label,pack(values),None))
    raw=array.array('I',[len(entries)])
    for _,w,_ in entries:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()
def native_reference(domain):
    from coordinate_geometry_reference import evaluate
    return evaluate(domain)
def expected(domain):
    e=native_reference(domain);w=[0]*OUTPUT_WORDS;w[:4]=[0,0x43475631,1,len(e['arcs'])];w[4:6]=words64(n.bits(e['distance']));w[6:8]=[int(e['contains']),len(e['breaks'])]
    for at,key in [(8,'measure'),(10,'cosine'),(12,'sine')]:w[at:at+2]=words64(n.bits(e[key]))
    for i,(start,end) in enumerate(e['arcs']):w[16+i*4:20+i*4]=words64(n.bits(start))+words64(n.bits(end))
    for i,value in enumerate(e['breaks']):w[4112+i*2:4114+i*2]=words64(n.bits(value))
    return w,e
def compare(block,domain):
    w,e=expected(domain)
    assert list(block)==w,('common geometry bits',domain,next((i for i,(a,b) in enumerate(zip(block,w)) if a!=b),None))
    return e
def validate_rejection(block,name):assert name.startswith('reject/coordinate-common-geometry/') and list(block)==[64]+[0]*(OUTPUT_WORDS-1)
