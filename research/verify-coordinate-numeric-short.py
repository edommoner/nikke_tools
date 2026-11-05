"""Strict bit comparison to the selected common CPU recipe, not host libm."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_coordinate_numeric_v1 as numeric
from portable_coordinate_numeric_cases import fixtures
s=importlib.util.spec_from_file_location('common_numeric_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
SOURCE='gpu/coordinate_numeric_probe.slang';INPUT_WORDS=12;OUTPUT_WORDS=16;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)
def words64(x):return [x&0xffffffff,x>>32]
def prepare():
    numeric.check_schema(ROOT);entries=[]
    for name,op,a,b in fixtures():entries.append(('coordinate-common-v1/'+name,[numeric.MAGIC,1,op,0,*words64(a),*words64(b),0,0,0,0],(op,a,b)))
    for label,op,a,b in [('nan',1,0x7ff8000000000000,0),('infinity',1,0x7ff0000000000000,0),('radian-range',2,numeric.TAU+1,0),('acos-range',4,numeric.ONE+1,0),('negative-root',5,numeric.SIGN|1,0),('reserved-b',1,0,1),('atan-nan-x',3,0,0x7ff8000000000000)]:
        entries.append(('reject/coordinate-common-v1/'+label,[numeric.MAGIC,1,op,0,*words64(a),*words64(b),0,0,0,0],None))
    seed=entries[0][1]
    for label,at,value in [('magic',0,0),('version',1,2),('opcode',2,6),('reserved',3,1),('tail',11,1)]:
        w=list(seed);w[at]=value;entries.append(('reject/coordinate-common-v1/'+label,w,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def native_reference(domain):
    op,a,b=domain
    pair=(numeric.sincos_degrees(a) if op==1 else numeric.sincos_radians(a) if op==2 else
        (numeric.atan2_bits(a,b),0) if op==3 else (numeric.acos_bits(a),0) if op==4 else (numeric.sqrt_bits(a),0))
    return dict(reference_kind='deterministic-common-cpu',contract=numeric.PROFILE,contract_sha256=numeric.contract_sha256(),results=[f'{v:016x}' for v in pair])
def compare(block,domain):
    e=native_reference(domain);a,b=(int(v,16) for v in e['results']);expected=[0,numeric.MAGIC,domain[0],1,*words64(a),*words64(b),*([0]*8)]
    assert list(block)==expected,('common numeric bits',domain)
    return e
def validate_rejection(block,name):assert name.startswith('reject/coordinate-common-v1/') and list(block)==[64]+[0]*15
