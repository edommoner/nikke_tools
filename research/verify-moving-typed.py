"""Whole original battles, shared motion, typed ownership and physical packets."""
import array,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
typed=module('moving_typed_actor','research/verify-coordinate-typed-actor-short.py')
motion=module('moving_typed_motion','research/verify-enemy-movement.py')
groups=module('moving_typed_groups','research/verify-coordinate-group-short.py')
from portable_moving_typed_cases import fixtures,prepare as prepare_case
from portable_moving_typed_wire import compile_battle,INPUT,OUTPUT,LOGICAL_BASE,MOVEMENT_BASE,MOVEMENT_OUT,AIM_BASE,AIM_WORDS
from world_moving_typed_native import observe
from portable_moving_typed_contracts import verify
from portable_skill_history import require_capacity,compare_and_project
SOURCE='gpu/world_moving_typed_entry.slang';STRICT_WIRE_DIMENSIONS=True;suite=SimpleNamespace(INPUT=INPUT,OUTPUT=OUTPUT)
cross=typed.cross;NATIVE_COMPARISON_CONTEXT=typed.NATIVE_COMPARISON_CONTEXT

def prepare():
    rows=[]
    for raw in fixtures():
        c,p=prepare_case(raw);words,meta,actors,scene=compile_battle(p,c);rows.append((c['name'],words,(c,meta,actors,scene)))
    seed=rows[0][1]
    for label,at,value in [('motion-magic',MOVEMENT_BASE,0),('motion-version',MOVEMENT_BASE+1,2),('policy',MOVEMENT_BASE+6,0),('motion-reserved',MOVEMENT_BASE+7,1),
        ('motion-nonfinite',MOVEMENT_BASE+272+5,0x7ff00000),('motion-kind',MOVEMENT_BASE+16,3),
        ('logical-magic',LOGICAL_BASE,0),('logical-count',LOGICAL_BASE+2,128),('logical-owner',LOGICAL_BASE+32,0),
        ('typed-owner-part',109968+2328+5,1),('typed-owner-unknown',109968+2328+6,999),('typed-aim-required',109968+14,0)]:
        words=list(seed);words[at]=value;rows.append(('reject/moving-typed/'+label,words,None))
    data=array.array('I',[len(rows)])
    for _,words,_ in rows:data.extend(words)
    if sys.byteorder!='little':data.byteswap()
    return rows,data.tobytes()

def native_reference(domain):
    n,_=observe(domain[0]);verify(domain[0],n);require_capacity(n)
    data=n['enemy_movement'];assert len(data['frames'])<=4096 and sum(len(f['segments']) for f in data['frames'])<=4096
    return n

def compare(block,domain):
    assert len(block)==OUTPUT and block[0]==0,'Complete successful moving typed output required'
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    clean=motion.compare_movement(block,domain,n,output_base=MOVEMENT_OUT)
    expected=[0]*AIM_WORDS
    frames=n['coordinate_typed_aim'];last=frames[-1] if frames else dict(candidates=[])
    for candidate in last['candidates']:
        at=candidate['slot']*4;expected[at:at+4]=struct.unpack('<4I',struct.pack('<2d',*candidate['point']))
    assert list(clean[AIM_BASE:AIM_BASE+AIM_WORDS])==expected,'Every frozen typed aim center and padding'
    clean[AIM_BASE:AIM_BASE+AIM_WORDS]=[0]*AIM_WORDS
    assert not any(clean[2032000:]),'All newly owned output must be fully compared before legacy projection'
    view,legacy,old_indices=compare_and_project(clean[:2032000],domain,n,indices)
    typed.parent.compare_observed(view,domain,legacy,old_indices)
    groups.compare_group_receipts(view[:1507328],domain,n,compare_packets=False)
    return n

def validate_rejection(block,name):assert name.startswith('reject/moving-typed/') and block[0]==64,(name,block[0])
