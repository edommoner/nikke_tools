"""Integer sum/product oracle uses Python bigint, not the GPU algorithm."""
import array,importlib.util,math,random,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_packet_integer_specs import LAYOUT as L,check_schema
SOURCE='gpu/packet_integer_probe.slang';INPUT_WORDS=L['INPUT'];OUTPUT_WORDS=L['OUTPUT'];STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)
s=importlib.util.spec_from_file_location('packet_integer_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
def bits(value):return list(struct.unpack('<II',struct.pack('<d',value)))
def fixtures():
    rows=[('empty',[],1),('signed-zero',[-0.],3),('lost-units',[float(2**53),1.,1.],1),
          ('multiply-before-round',[float(2**53),1.],3)]
    for count in [1,2,3,7,127,128]:
        for multiplier in [1,3,7,64,1024]:rows.append((f'max/{count}/{multiplier}',[math.nextafter(float(2**63),0.)]*count,multiplier))
    for exponent in range(53,70):
        # Reach large total exponents using legal per-packet amounts.
        count=2**max(0,exponent-62);value=float(2**min(exponent,62))
        if count<=128:
            for offset in [0.,1.,2.,3.]:rows.append((f'tie/{exponent}/{offset}',[value]*count+[offset] if count<128 else [value]*(count-1)+[value-offset],7))
    rng=random.Random(0x50495331)
    for i in range(192):
        count=rng.randrange(129);values=[float(rng.getrandbits(rng.randrange(1,63))) for _ in range(count)]
        rows.append((f'generated/{i}',values,rng.randrange(1,1025)))
    return rows
def prepare():
    check_schema(ROOT);rows=[]
    for name,values,multiplier in fixtures():
        words=[0]*INPUT_WORDS;words[:4]=[L['MAGIC'],1,len(values),multiplier]
        for i,value in enumerate(values):words[8+i*2:10+i*2]=bits(value)
        rows.append(('packet-integer/'+name,words,(values,multiplier)))
    seed=rows[2][1]
    for name,at,value in [('magic',0,0),('count',2,129),('multiplier-zero',3,0),('multiplier-large',3,1025),('reserved',4,1),('unused',14,1)]:
        words=list(seed);words[at]=value;rows.append(('reject/packet-integer/'+name,words,None))
    for name,value in [('fraction',.5),('negative',-1.),('nan',math.nan),('inf',math.inf),('signed-overflow',float(2**63))]:
        words=list(seed);words[8:10]=bits(value);rows.append(('reject/packet-integer/'+name,words,None))
    raw=array.array('I',[len(rows)])
    for _,words,_ in rows:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def native_reference(domain):
    values,multiplier=domain;total=sum(map(int,values))*multiplier
    return dict(exact_integer=str(total),rounded_bits=bits(float(total)))
def compare(block,domain):
    expected=native_reference(domain);n=int(expected['exact_integer'])
    words=[0,L['MAGIC'],n&0xffffffff,(n>>32)&0xffffffff,(n>>64)&0xffffffff,(n>>96)&0xffffffff,*expected['rounded_bits']]
    assert list(block)==words,('Exact packet integer reduction',domain)
    return expected
def validate_rejection(block,name):assert name.startswith('reject/packet-integer/') and list(block)==[64]+[0]*7
