"""Exact rational and CPython round(x,6) oracles; no host transcendental math."""
import array,math,random,struct,sys
from types import SimpleNamespace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import importlib.util
s=importlib.util.spec_from_file_location('round_cross',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
SOURCE='gpu/coordinate_round_probe.slang';INPUT_WORDS=4;OUTPUT_WORDS=6;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)
def bits(x):return struct.unpack('<Q',struct.pack('<d',x))[0]
def number(x):return struct.unpack('<d',struct.pack('<Q',x))[0]
def fixtures():
    values=[0.,-0.,1.,-1.,math.nextafter(0.,1.),-math.nextafter(0.,1.),sys.float_info.max,-sys.float_info.max]
    for numerator in range(-127,128):
        x=numerator/128;values.extend([math.nextafter(x,-math.inf),x,math.nextafter(x,math.inf)])
    for exponent in range(-25,36):
        for v in [1.,1.5,math.nextafter(2.,0.)]:
            for sign in [1,-1]:
                x=sign*math.ldexp(v,exponent);values.extend([math.nextafter(x,-math.inf),x,math.nextafter(x,math.inf)])
    rng=random.Random(0x434f5245)
    for _ in range(4096):values.append(number(rng.getrandbits(64)))
    for i in range(1,513):
        x=(i+.5)/1e6
        for sign in [1,-1]:values.extend([math.nextafter(sign*x,-math.inf),sign*x,math.nextafter(sign*x,math.inf)])
    return [('round-six/'+str(i),bits(x)) for i,x in enumerate(values) if math.isfinite(x)]
def prepare():
    rows=[(n,[v&0xffffffff,v>>32,0,0],v) for n,v in fixtures()]
    for i,v in enumerate([0x7ff0000000000000,0xfff0000000000000,0x7ff8000000000001,0xfff8000000000001,0x7ff0000000000001]):rows.append(('reject/round-six/nonfinite-'+str(i),[v&0xffffffff,v>>32,0,0],None))
    rows.extend([('reject/round-six/reserved-'+str(i),[0,0,1 if i==0 else 0,1 if i==1 else 0],None) for i in range(2)])
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def native_reference(value):
    x=number(value);rounded=round(x,6)
    return dict(input_bits=value,rounded_bits=bits(rounded),key_bits=0 if rounded==0 else bits(rounded))
def compare(block,value):
    r=native_reference(value);a=r['rounded_bits'];b=r['key_bits'];assert list(block)==[0,a&0xffffffff,a>>32,b&0xffffffff,b>>32,0x43523631],(hex(value),block,r);return r
def validate_rejection(block,name):assert name.startswith('reject/round-six/') and list(block)==[64,0,0,0,0,0]
