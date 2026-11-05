"""Actual shared battle and direct pool geometry selection, one common backend suite."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_pool_cases import fixtures
from portable_coordinate_scene_specs import compile_scene,LAYOUT as C,bits
from world_coordinate_pool_native import observe
spec=importlib.util.spec_from_file_location('coordinate_pool_parent',ROOT/'research/verify-world-heal-share-short.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
BASE_INPUT=104400;BASE_OUTPUT=786432
SOURCE='gpu/world_coordinate_pool_entry.slang';INPUT_WORDS=BASE_INPUT+C['INPUT'];OUTPUT_WORDS=1048576;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS,inspect_native=lambda case:observe(case));cross=parent.cross

def prepare():
    entries=[]
    for case in fixtures():
        w,m,b=parent.suite.compile_case(case);assert len(w)==BASE_INPUT
        side,_=compile_scene(case['coordinate_sidecar']);entries.append((case['name'],w+side,(case,m,b)))
    seed=entries[0][1];at=BASE_INPUT+C['ROW_BASE']
    for name,offset,value in [('binding-kind',at,6),('binding-ordinal',at+3,100),('binding-hp',at+21,0),('binding-count',BASE_INPUT+2,0),('binding-slot',at+5,127)]:
        w=list(seed);w[offset]=value;entries.append(('reject/coordinate-pool-'+name,w,None))
    packed=array.array('I',[len(entries)])
    for _,w,_ in entries:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def native_reference(domain):return observe(domain[0])
def expected_snapshot(snapshot):
    out=array.array('I',[0])*(OUTPUT_WORDS-BASE_OUTPUT);out[:4]=array.array('I',bits(snapshot['time'])+[len(snapshot['all']),len(snapshot['parts'])])
    for label,base in [('all',8),('parts',8+C['ROWS']*4)]:
        for i,row in enumerate(snapshot[label]):out[base+i*4:base+i*4+4]=array.array('I',row)
    return out
def compare(block,domain):
    expected=native_reference(domain);parent.compare_expected(block[:BASE_OUTPUT],domain,{k:v for k,v in expected.items() if k!='coordinate_pool'})
    assert block[BASE_OUTPUT:]==expected_snapshot(expected['coordinate_pool']),(domain[0]['name'],'direct world pool geometry snapshot')
    return expected
def validate_rejection(block,name):assert name.startswith('reject/coordinate-pool-') and block[0]==64
