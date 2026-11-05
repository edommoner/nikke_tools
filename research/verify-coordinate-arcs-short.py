"""Common interval algebra, compared to canonical aim helpers, not a battle."""
import array,importlib.util,math,random,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from calculator import aim
from portable_coordinate_scene_specs import bits
s=importlib.util.spec_from_file_location('arc_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
SOURCE='gpu/coordinate_arc_probe.slang';INPUT_WORDS=4104;OUTPUT_WORDS=4100;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)

def fixtures():
    rows=[]
    def add(label,a,b):
        for op in (1,2,3):rows.append((label+'/'+str(op),op,a,b))
    add('empty',[],[]);add('one-empty',[(0.,1.)],[])
    add('adjacent',[(0.,1.)],[(1.,2.)])
    add('nested',[(0.,6.)],[(1.,2.),(3.,4.)])
    add('endpoint-ulp',[(0.,1.)],[(math.nextafter(1.,0.),2.)])
    add('full',[(0.,math.tau)],[(0.,math.tau)])
    add('wrapped',[(0.,.5),(5.,math.tau)],[(.25,1.),(4.,5.5)])
    add('signed-zero',[(-0.,1.)],[(0.,2.)])
    # Maximum legal disjoint operands: union emits all 1024 intervals.
    add('capacity-1024',[(i/256.,i/256.+1/1024.) for i in range(512)],
        [(i/256.+1/512.,i/256.+3/1024.) for i in range(512)])
    add('capacity-subtract-1024',[(i/256.,i/256.+3/1024.) for i in range(512)],
        [(i/256.+1/1024.,i/256.+2/1024.) for i in range(512)])
    rng=random.Random(0x41524353)
    for i in range(32):
        def intervals():
            points=sorted(rng.sample(range(1,6000),2*rng.randrange(1,16)))
            return [(x/1000.,y/1000.) for x,y in zip(points[::2],points[1::2])]
        add('random-'+str(i),intervals(),intervals())
    return rows

def prepare():
    entries=[]
    for name,op,a,b in fixtures():
        words=[0]*INPUT_WORDS;words[:5]=[0x43415243,1,op,len(a),len(b)]
        for base,values in [(8,a),(2056,b)]:
            for i,(start,end) in enumerate(values):words[base+i*4:base+i*4+4]=bits(start)+bits(end)
        entries.append(('coordinate-arcs/'+name,words,(op,a,b)))
    seed=entries[6][1]
    for label,offset,value in [('magic',0,0),('op',2,4),('count',3,513),('reserved',5,1),('nan',9,0x7ff80000),('negative',9,0xbff00000),('inverted',11,0),('unused',12,1)]:
        w=list(seed);w[offset]=value;entries.append(('reject/coordinate-arcs-'+label,w,None))
    w=list(seed);w[3]=2;w[12:16]=bits(.5)+bits(1.5);entries.append(('reject/coordinate-arcs-overlap',w,None))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()

def native_reference(domain):
    op,a,b=domain;values={1:aim._union,2:aim._intersect,3:aim._subtract}[op](a,b)
    return dict(intervals=values)

def compare(block,domain):
    expected=native_reference(domain);values=expected['intervals'];words=[0]*OUTPUT_WORDS
    words[:3]=[0,0x43415243,len(values)]
    for i,(start,end) in enumerate(values):words[4+i*4:8+i*4]=bits(start)+bits(end)
    assert list(block)==words,('angular interval bits',domain[0])
    return expected

def validate_rejection(block,name):
    assert name.startswith('reject/coordinate-arcs-') and list(block)==[64]+[0]*(OUTPUT_WORDS-1)
