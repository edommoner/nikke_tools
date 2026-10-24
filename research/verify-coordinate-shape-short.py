"""The exact shape math used by world skill selection, as a short GPU probe."""
import array,importlib.util,math,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_area_specs import rotation_coefficients
from portable_coordinate_scene_specs import bits
from portable_coordinate_shape_cases import fixtures
s=importlib.util.spec_from_file_location('shape_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
SOURCE='gpu/coordinate_shape_probe.slang';INPUT_WORDS=24;OUTPUT_WORDS=8;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=24,OUTPUT=8,inspect_native=lambda c:native_reference((c,)))
def native_reference(domain):
    c=domain[0];d=c['shape'].dist(*c['point']);b=0x7ff8000000000000 if math.isnan(d) else struct.unpack('<Q',struct.pack('<d',d))[0]
    return dict(distance_bits=b,contains=c['shape'].contains(*c['point'],c['grow']))
def prepare():
    entries=[]
    for c in fixtures():
        sh=c['shape'];co,si=rotation_coefficients(sh);w=[0x43534831,1,1 if sh.is_circle else 2,0]+sum((bits(v) for v in (sh.x,sh.y,sh.r,sh.w,sh.h,co,si,*c['point'],c['grow'])),[]);entries.append((c['name'],w,(c,)))
    seed=entries[0][1];rect=entries[45][1]
    for label,w,at,value in [('magic',seed,0,0),('kind',seed,2,3),('cos-nan',seed,15,0x7ff80000),('matrix-norm',seed,15,0),('width-zero',rect,11,0),('grow-negative',seed,23,0xbff00000),('point-nan',seed,19,0x7ff80000),('reserved',seed,3,1)]:
        v=list(w);v[at]=value;entries.append(('reject/coordinate-shape-'+label,v,None))
    packed=array.array('I',[len(entries)])
    for _,w,_ in entries:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def compare(block,domain):
    e=native_reference(domain);v=e['distance_bits'];assert list(block)==[0,0x43534831,v&0xffffffff,v>>32,int(e['contains']),0,0,0],(domain[0]['name'],'shape distance/contains bits');return e
def validate_rejection(block,name):assert name.startswith('reject/coordinate-shape-') and list(block)==[64,0,0,0,0,0,0,0]
