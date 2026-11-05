"""Exact rational oracle, independently rounded by Python bigint true division."""
import array,importlib.util,random,struct,sys
from pathlib import Path
from fractions import Fraction
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
SOURCE='gpu/packet_ratio_probe.slang';INPUT_WORDS=8;OUTPUT_WORDS=8;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=8,OUTPUT=8);MAGIC=0x50525631
s=importlib.util.spec_from_file_location('ratio_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
def fixtures():
    rows=[]
    for d in range(1,1025):
        for n in [0,1,d-1,d,d+1,2**53-1,2**53+1,2**64+3,2**80-1,2**119+7,2**127+1,2**128-1]:rows.append((f'divisor-{d}/n-{n}',n,d))
    for h in [52,53,54,55,56,63,64,65,118,119,120,126,127]:
        for d in [1,2,3,5,7,8,1023,1024]:
            for tail in [-3,-2,-1,0,1,2,3]:
                n=(1<<h)+tail
                if 0<=n<2**128:rows.append((f'round-{h}/{d}/{tail}',n,d))
    rng=random.Random(0x50525631)
    for i in range(1024):rows.append((f'generated-{i}',rng.getrandbits(128),rng.randrange(1,1025)))
    return rows
def wire(n,d):return [MAGIC,1,*[(n>>(32*i))&0xffffffff for i in range(4)],d,0]
def prepare():
    rows=[('packet-ratio/'+label,wire(n,d),(n,d)) for label,n,d in fixtures()]
    for label,at,value in [('magic',0,0),('version',1,2),('reserved',7,1),('zero-divisor',6,0),('large-divisor',6,1025)]:
        w=wire(2**128-1,3);w[at]=value;rows.append(('reject/packet-ratio/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def native_reference(domain):
    n,d=domain;v=float(Fraction(n,d));assert v==n/d
    return dict(reference_kind='exact-integer-ratio-cpu',numerator=str(n),divisor=d,bits=list(struct.unpack('<II',struct.pack('<d',v))))
def compare(block,domain):
    e=native_reference(domain);assert list(block)==[0,MAGIC,domain[1],0,*e['bits'],0,0],('One-round integer ratio',domain);return e
def validate_rejection(block,name):assert name.startswith('reject/packet-ratio/') and list(block)==[64]+[0]*7
