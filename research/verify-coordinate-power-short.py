"""Strict common CPU interval reference; MPFR remains an independent audit."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_coordinate_power_v1 as p
from portable_coordinate_power_cases import fixtures
s=importlib.util.spec_from_file_location('power_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
SOURCE='gpu/coordinate_power_probe.slang';INPUT_WORDS=8;OUTPUT_WORDS=8;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)
def words64(x):return [x&0xffffffff,x>>32]
def prepare():
    p.check_schema(ROOT);rows=[('coordinate-power/'+name,[0x43505631,1,0,0,*words64(x),*words64(y)],(x,y)) for name,x,y in fixtures()]
    for label,x,y in [('negative-x',p.bits(-.5),p.bits(2.55)),('x-above-one',p.ONE+1,p.bits(2.55)),('nan',0x7ff8000000000000,p.ONE),('infinity',0x7ff0000000000000,p.ONE),('exponent-zero',p.ONE,0),('exponent-negative',p.ONE,p.bits(-1.)),('exponent-low',p.ONE,p.MIN_EXPONENT-1),('exponent-high',p.ONE,p.MAX_EXPONENT+1)]:rows.append(('reject/coordinate-power/'+label,[0x43505631,1,0,0,*words64(x),*words64(y)],None))
    seed=rows[0][1]
    for label,at,value in [('magic',0,0),('version',1,2),('reserved',2,1)]:
        w=list(seed);w[at]=value;rows.append(('reject/coordinate-power/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def native_reference(domain):return dict(reference_kind='deterministic-common-cpu',contract=p.PROFILE,bits=p.evaluate(*domain))
def compare(block,domain):
    e=native_reference(domain);assert list(block)==[0,0x43505631,*words64(e['bits']),0,0,0,0],('unit power',domain);return e
def validate_rejection(block,name):assert name.startswith('reject/coordinate-power/') and list(block)==[64]+[0]*7
