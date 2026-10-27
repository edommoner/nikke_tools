"""Shared integer-only slot policy proof, not a complete battle consumer."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from impact_specs import ActorHandle
from named_generation_locks import LockSnapshot
from world_actor_runtime import ActorSnapshot
from lock_delivery_policy import MODEL,select
SOURCE='gpu/lock_delivery_probe.slang';INPUT=1032;OUTPUT=16;MAGIC=0x4c443031
suite=SimpleNamespace(SOURCE=SOURCE,INPUT=INPUT,OUTPUT=OUTPUT)
spec=importlib.util.spec_from_file_location('delivery_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)

def fixtures():
    rows=[]
    for count in (0,1,2,5,15,128):
        frozen=[[i%6,i//6,1] for i in range(count)]
        for hit in sorted({1,max(1,count),min(256,count+1),256}):
            rows.append(dict(name=f'lock-delivery/cycle-{count}-{hit}',revision=7,hit=hit,hits=256,frozen=frozen,current=[[*h,1] for h in reversed(frozen)]))
    for kind in range(6):
        frozen=[[kind,0,1],[5,99,1]]
        for status in ('ready','missing','stale','dead'):
            current=[[*frozen[1],1]]
            if status!='missing':current.append([kind,0,2 if status=='stale' else 1,int(status!='dead')])
            rows.append(dict(name=f'lock-delivery/typed-{kind}-{status}',revision=11,hit=1,hits=3,frozen=frozen,current=current))
    rows.append(dict(name='lock-delivery/integer-boundaries',revision=0x7fffffff,hit=256,hits=256,frozen=[[5,0x0fffffff,0x7fffffff]],current=[[5,0x0fffffff,0x7fffffff,1]]))
    return rows

def native_reference(case):
    frozen=LockSnapshot(case['revision'],tuple(ActorHandle(*h) for h in case['frozen']))
    views=[ActorSnapshot(ActorHandle(*r[:3]),str(i),bool(r[3])) for i,r in enumerate(case['current'])]
    chosen=select(frozen,case['hit'],case['hits'],views,model=MODEL);h=chosen.handle
    return dict(model=MODEL,status=chosen.status,index=chosen.index,handle=[int(h.kind),h.identity,h.generation] if h else None,current_generation=chosen.current_generation)

def compile_case(case):
    native_reference(case)
    words=[case['revision'],len(case['frozen']),case['hit'],case['hits'],len(case['current']),MAGIC,0,0]+[0]*1024
    for i,h in enumerate(case['frozen']):words[8+i*4:12+i*4]=[*h,0]
    for i,r in enumerate(case['current']):words[520+i*4:524+i*4]=r
    return words

def compare(block,case):
    result=native_reference(case);h=result['handle'] or [0xffffffff,0,0]
    expected=[0,result['status'],result['index'],*h,result['current_generation'],case['revision'],case['hit'],case['hits'],len(case['frozen']),len(case['current']),MAGIC,0,0,0]
    if list(block)!=expected:raise AssertionError((case['name'],list(block),expected))
    return result

def prepare():
    rows=[(c['name'],compile_case(c),c) for c in fixtures()]
    seed=next(w for n,w,_ in rows if n=='lock-delivery/cycle-2-1')
    bad=[('revision',0,0x80000000),('snapshot-capacity',1,129),('zero-hit',2,0),('late-hit',2,257),('hit-total',3,0),('view-capacity',4,129),('model',5,0),('reserved',6,1),('kind',8,6),('identity',9,0x10000000),('generation',10,0),('snapshot-reserved',11,1),('alive',523,2),('snapshot-padding',8+127*4,1),('view-padding',520+127*4,1)]
    for name,at,value in bad:
        words=list(seed);words[at]=value;rows.append(('reject/'+name,words,None))
    for name,start in [('duplicate-snapshot',8),('duplicate-view',520)]:
        words=list(seed);words[start+4:start+8]=words[start:start+4];rows.append(('reject/'+name,words,None))
    data=array.array('I',[len(rows)])
    for _,words,_ in rows:data.extend(words)
    if sys.byteorder!='little':data.byteswap()
    return rows,data.tobytes()

def validate_rejection(block,name):
    if list(block)!=[64]+[0]*15:raise AssertionError(('Incomplete rejection',name,list(block)))
