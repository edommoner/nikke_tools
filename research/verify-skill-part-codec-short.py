"""Whole-output codec oracle, including final slot, reuse and periodic sentinel."""
import array,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_specs import LIMITS as L
from portable_parts_skill_specs import BASE,verify_layout
spec=importlib.util.spec_from_file_location('part_codec_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=6,OUTPUT=786432)
CASES=[('first-clear',0,.1,0.),('last-reuse',2047,3e8,-0.),('middle-set',1024,0.,123.5),('reject-overflow',2048,1.,2.)]
def bits(v):return list(struct.unpack('<II',struct.pack('<d',v)))
def native_reference(domain):
    _,index,first,second=domain
    return dict(status=0,index=index,first=bits(first),second=bits(second),sentinel=0x50415254)
def prepare():
    verify_layout(L);entries=[];packed=array.array('I',[len(CASES)])
    for d in CASES:
        words=[d[1],*bits(d[2]),*bits(d[3]),0x50415254];entries.append(('part-codec-'+d[0],words,d if d[1]<2048 else None));packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def expected_block(domain):
    n=native_reference(domain);block=array.array('I',[0])*suite.OUTPUT
    block[1:6]=array.array('I',n['first']+n['second']+[n['sentinel']])
    block[L['LANDING_STATE_BASE']+n['index']*8+7]=n['sentinel']
    block[BASE+n['index']*2:BASE+n['index']*2+2]=array.array('I',n['second'])
    return block
def compare(block,domain):
    if list(block)!=list(expected_block(domain)):raise AssertionError((domain[0],'codec output or neighbor corruption'))
    return native_reference(domain)
def validate_rejection(block,name):
    if name!='part-codec-reject-overflow' or block[0]!=64 or any(block[1:]):raise AssertionError('Wrong codec rejection')
