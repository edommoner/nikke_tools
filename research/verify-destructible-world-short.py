"""Existing native graph clock + declared typed lifecycle versus shared Slang."""
import array,copy,importlib.util,struct,sys,types
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from destructible_world_runtime import DestructibleWorld,compile_bindings
from destructible_world_cases import fixtures
from portable_world_schedule_specs import compile_schedule,OUTCOMES
from impact_specs import ActorHandle,HitFamily,HitOutcome,Impact
from world_schedule_native import cleared_run
suite=types.SimpleNamespace(INPUT=5120)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
cross=load('dw_cross','research/summarize-portable-cross-gpu.py')
old=load('dw_state','research/verify-destructible-target-core-short.py')
words=old.words

def compile_case(c):
 patterns,parsed,bindings=compile_bindings(c['nodes'],c['bindings'])
 if not 1<=len(c['ops'])<=32:raise ValueError('World operation capacity exceeded')
 through=max(float(op[5]) for op in c['ops']);graph,_=compile_schedule(dict(patterns=patterns,duration=through,finish=False))
 w=[0]*5120;w[:2320]=graph;w[2320]=len(bindings);w[3864]=len(c['ops'])
 for slot,b in enumerate(bindings):
  at=2328+slot*12;owner=[0xffffffff,0,0] if b.owner is None else [int(b.owner.kind),b.owner.identity,b.owner.generation]
  w[at:at+8]=[b.node,int(b.handle.kind),b.handle.identity,*words(b.capacity),*owner]
 for i,(op,slot,kind,identity,generation,t,amount,credit,policy) in enumerate(c['ops']):
  at=3872+i*32;w[at:at+12]=[op,slot,kind,identity,generation,*words(t),*words(amount),*words(credit),policy]
 return w

def prepare():
 rows=[(c['name'],compile_case(c),c) for c in fixtures()];seed=rows[0][1]
 changes=[('magic',0,0),('world-frame-injection',2,1),('binding-count',2320,129),('binding-node',2328,32),('binding-kind',2329,1),('binding-reserved',2328+8,1),('unused-binding',2328+12,1),('operation-reserved',3872+12,1),('unused-operation',3872+len(fixtures()[0]['ops'])*32,1),('step-count',3864,33)]
 for name,at,value in changes:
  w=list(seed);assert w[at]!=value;w[at]=value;rows.append(('reject/destructible-world/'+name,w,None))
 c=next(c for c in fixtures() if c['name'].endswith('all-targets-cleared'));w=compile_case(c);w[2328+12+1]=w[2329];w[2328+12+2]=w[2330];rows.append(('reject/destructible-world/duplicate-identity',w,None))
 c=next(c for c in fixtures() if c['name'].endswith('finish-without-first-frame'));w=compile_case(c);w[3864]=2;rows.append(('reject/destructible-world/after-finish',w,None))
 packed=array.array('I',[len(rows)])
 for _,w,_ in rows:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 return rows,packed.tobytes()

def clock_states(world):
 rows=[]
 for r in world.clock._runs:rows.append([int(r.active),r.opens,*words(r.start_t),r.fired,0,int(cleared_run(r)),0,*r.consumed_after,*([0]*(8-len(r.consumed_after))),*r.consumed_until,*([0]*(8-len(r.consumed_until)))])
 return rows+[[0]*24 for _ in range(32-len(rows))]
def native_reference(c):
 world=DestructibleWorld(c['nodes'],c['bindings']);history=[];log=[];operations=[];opening=world.clock._open;closing=world.clock._close
 def opened(run,t,trigger,events):
  opening(run,t,trigger,events);labels=[n if o is None else f'{n}({o})' for n,o in run.p.after];log.append([1,run.p.idx,labels.index(trigger),*words(t),0])
 def closed(run,t,outcome,events):
  closing(run,t,outcome,events);history.append([run.p.idx,OUTCOMES[outcome],*words(t)]);log.append([2,run.p.idx,OUTCOMES[outcome],*words(t),0])
 with patch.object(world.clock,'_open',opened),patch.object(world.clock,'_close',closed):
  for op,slot,kind,identity,generation,t,amount,credit,policy in c['ops']:
   if op!=3 and not world.clock._ends['start']:history.append([32,0,*words(t)])
   advanced=False
   if op==3:world.finish(t)
   else:advanced=world.advance(t)
   answer=dict(op=op,advanced=advanced,finished=world.finished)
   if op==1:
    result=world.hit(slot,Impact('owner0',ActorHandle(kind,identity,generation),HitFamily.SKILL,HitOutcome(policy),float(amount),float(credit)))
    if result['notice'] is not None:result['notice']['time']=old.bits(result['notice']['time'])
    answer.update(result,took=old.bits(result['took']))
   elif op==2:answer['selected']=list(world.targets.select([i for i in range(32) if policy&(1<<i)]))
   answer.update(state=old.snapshot(world.targets),clock=clock_states(world),history_count=len(history),log_count=len(log));operations.append(answer)
 return dict(scope='existing_BossScript_clock_and_declared_typed_world_only',operations=operations,history=history,log=log)

def decode(block,c):
 assert block[0]==0 and block[1]==len(c['ops']) and block[2]==0 and block[3]==len(c['bindings']),(c['name'],block[:4])
 bit=lambda at:struct.pack('<II',*block[at:at+2]).hex();operations=[]
 for step,o in enumerate(c['ops']):
  at=20000+step*2640;assert block[at]==o[0] and block[at+1]==0;answer=dict(op=o[0],advanced=bool(block[at+2]),finished=bool(block[at+20]))
  if o[0]==1:
   broken=bool(block[at+4]);notice=None
   if broken:notice=dict(handle=list(block[at+10:at+13]),owner=None if block[at+7]==0xffffffff else list(block[at+7:at+10]),time=bit(at+13))
   else:assert block[at+7]==0xffffffff and not any(block[at+8:at+15])
   answer.update(delivered=bool(block[at+3]),broken=broken,took=bit(at+5),notice=notice)
  elif o[0]==2:answer['selected']=[i for i in range(128) if block[at+16+i//32]&(1<<(i%32))]
  state=[]
  for slot in range(128):
   p=at+32+slot*14
   if block[p+2]==0:assert not any(block[p:p+14]);continue
   assert slot<len(c['bindings']) and block[p+13]==0
   state.append(dict(slot=slot,handle=list(block[p:p+3]),owner=None if block[p+10]==0xffffffff else list(block[p+10:p+13]),alive=bool(block[p+3]),remaining=bit(p+4),capacity=bit(p+6),expires=bit(p+8)))
  answer.update(state=state,clock=[list(block[at+1824+n*24:at+1824+(n+1)*24]) for n in range(32)],history_count=block[at+21],log_count=block[at+22]);operations.append(answer)
 w=16;history=[list(block[w+784+i*4:w+784+(i+1)*4]) for i in range(block[w+1])];log=[list(block[w+2832+i*6:w+2832+(i+1)*6]) for i in range(block[w+2])]
 return dict(scope='existing_BossScript_clock_and_declared_typed_world_only',operations=operations,history=history,log=log)
def compare(block,domain):
 expected=native_reference(domain);actual=decode(block,domain);assert actual==expected,(domain['name'],actual,expected);return expected
def validate_rejection(block,name):assert name.startswith('reject/destructible-world/') and block[0]==64 and block[2]==64,(name,block[:3])
