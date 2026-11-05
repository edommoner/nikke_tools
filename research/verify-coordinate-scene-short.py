"""Whole-buffer native oracle for shared coordinate descriptor/selection primitives."""
import array,copy,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_scene_specs import compile_scene,bits,LAYOUT as L,MAGIC
from portable_coordinate_scene_cases import fixtures
from world_coordinate_scene_native import observe
spec=importlib.util.spec_from_file_location('coordinate_scene_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=L['INPUT'],OUTPUT=L['OUTPUT']);INPUT_WORDS=L['INPUT'];OUTPUT_WORDS=L['OUTPUT'];STRICT_WIRE_DIMENSIONS=True
SOURCE='gpu/coordinate_scene_probe.slang'
def native_reference(domain):return observe(domain[0])[0]
suite.inspect_native=lambda case:observe(case)[0]
def prepare():
    entries=[]
    for case in fixtures():
        words,meta=compile_scene(case);entries.append((case['name'],words,(case,words,meta)))
    seed=entries[0][1];base=L['ROW_BASE'];op=L['OP_BASE'];bad=[('magic',0,0),('count',2,128),('kind',base,2),('shape',base+4,3),('duplicate-id',base+L['ROW_WORDS']+1,0),('radius',base+11,0xbff00000),('nan',base+7,0x7ff80000),('reserved',base+22,1),('operation',op,99),('negative-time',op+3,0xbff00000),('body-slot',base+5,0)]
    for label,at,value in bad:
        words=list(seed);words[at]=value;entries.append(('reject/coordinate-scene-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def expected_block(domain):
    case,words,_=domain;n=native_reference(domain);out=array.array('I',[0])*L['OUTPUT'];out[1:4]=array.array('I',[len(n['snapshots']),words[2],MAGIC]);out[L['DESC']:L['STATE']]=array.array('I',words[L['ROW_BASE']:L['OP_BASE']])
    for i,s in enumerate(n['states']):
        at=L['STATE']+i*8;out[at:at+8]=array.array('I',[s['generation'],int(s['alive']),*bits(s['dealt']),*bits(s['start']),s['hits'],0])
    for i,s in enumerate(n['snapshots']):
        at=L['QUERIES']+i*L['SNAPSHOT'];out[at:at+4]=array.array('I',bits(s['time'])+[len(s['all']),len(s['parts'])])
        for label,base in [('all',at+8),('parts',at+8+L['ROWS']*4)]:
            for j,row in enumerate(s[label]):out[base+j*4:base+j*4+4]=array.array('I',row)
    return out
def compare(block,domain):
    expected=expected_block(domain)
    if block!=expected:raise AssertionError((domain[0]['name'],'coordinate descriptor/order/lifetime or neighbor corruption',next((i for i,(a,b) in enumerate(zip(block,expected,strict=True)) if a!=b),None)))
    return native_reference(domain)
def validate_rejection(block,name):
    assert name.startswith('reject/coordinate-scene-') and block[0]==64 and not any(block[1:])
