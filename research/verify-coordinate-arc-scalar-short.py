"""Canonical arc wrap, shift and compensated measure, with whole-word checks."""
import array,importlib.util,math,random,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from calculator import aim
from portable_coordinate_scene_specs import bits
s=importlib.util.spec_from_file_location('scalar_arc_sets',ROOT/'research/verify-coordinate-arcs-short.py');sets=importlib.util.module_from_spec(s);s.loader.exec_module(sets);cross=sets.cross
SOURCE='gpu/coordinate_arc_scalar_probe.slang';INPUT_WORDS=2056;OUTPUT_WORDS=4104;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)

def fixtures():
    rows=[]
    values=[0.,-0.,math.tau,-math.tau,2*math.tau,-2*math.tau,1e-300,-1e-300,
        math.ulp(0.),-math.ulp(0.),sys.float_info.max,-sys.float_info.max,
        math.nextafter(math.tau,0),math.nextafter(math.tau,math.inf),2.**53,-2.**53]
    rng=random.Random(0x4152434d)
    for _ in range(256):
        value=struct.unpack('<d',struct.pack('<Q',rng.getrandbits(64)))[0]
        if math.isfinite(value):values.append(value)
    for i,x in enumerate(values):rows.append(('modulo/'+str(i),1,x,0.,[]))
    threshold=math.tau-1e-12
    for i,x in enumerate([-math.tau,.25,5.,-1e-300,sys.float_info.max]):
        for j,y in enumerate([-1.,0.,-0.,math.nextafter(threshold,0),threshold,
                math.nextafter(threshold,math.inf),math.tau,2*math.tau,1e-300,.5]):
            rows.append((f'create/{i}/{j}',2,x,y,[]))
    compensation=[(0.4408772628779949,0.9477972873102967),(1.042371601403538,1.1025418276869412),
        (1.13445403075805,2.9804215267660825),(3.8381573493624006,4.04802712142726),
        (4.706755435830232,5.7981692947749846)]
    operands=[('empty',[]),('zero-width',[(math.tau,math.tau)]),('compensated',compensation)]
    operands += [(name,a) for name,op,a,b in sets.fixtures() if op==1]
    for name,a in operands:
        rows.append(('measure/'+name,3,0.,0.,a))
        for j,by in enumerate([-math.tau,0.,.3,-1e-300,sys.float_info.max]):
            rows.append((f'shift/{name}/{j}',4,by,0.,a))
    for op in (8,9):
        for i,x in enumerate([0.,1.,math.tau,-1e-300]):
            for j,length in enumerate([-1.,0.,1e-300,.5,math.tau]):
                rows.append((f'generated-cover/{op}/{i}/{j}',op,x,length,[(0.,math.tau)]))
    return rows

def prepare():
    entries=[]
    for name,op,x,y,a in fixtures():
        w=[0]*INPUT_WORDS;w[:8]=[0x43415331,1,op,len(a),*bits(x),*bits(y)]
        for i,(start,end) in enumerate(a):w[8+i*4:12+i*4]=bits(start)+bits(end)
        entries.append(('coordinate-arc-scalar/'+name,w,(op,x,y,a)))
    seed=next(w for name,w,d in entries if name=='coordinate-arc-scalar/measure/compensated')
    for label,offset,value in [('magic',0,0),('op',2,5),('count',3,513),('nan',5,0x7ff80000),('reserved-scalar',4,1),('negative-interval',9,0xbff00000),('inverted',11,0),('unused',28,1)]:
        w=list(seed);w[offset]=value;entries.append(('reject/coordinate-arc-scalar-'+label,w,None))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()

def native_reference(domain):
    op,x,y,a=domain
    if op==1:return dict(intervals=[],scalar=x%math.tau)
    value=(aim._arc(x,y) if op==2 else a if op==3 else aim._shift(a,x) if op==4
           else aim._subtract(a,aim._arc(x,y)) if op==8 else aim._intersect(a,aim._arc(x,y)))
    return dict(intervals=value,scalar=float(aim._measure(value)))

def compare(block,domain):
    e=native_reference(domain);words=[0]*OUTPUT_WORDS;words[:3]=[0,0x43415331,len(e['intervals'])];words[4:6]=bits(e['scalar'])
    for i,(start,end) in enumerate(e['intervals']):words[8+i*4:12+i*4]=bits(start)+bits(end)
    assert list(block)==words,('arc scalar bits',domain[:3])
    return e

def validate_rejection(block,name):assert name.startswith('reject/coordinate-arc-scalar-') and list(block)==[64]+[0]*(OUTPUT_WORDS-1)
