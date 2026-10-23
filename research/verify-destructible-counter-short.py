"""Declared typed worlds feed the unchanged shared counter/child executor."""
import array,copy,dataclasses,importlib.util,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
import engine_worker
from destructible_counter_cases import fixtures
from destructible_world_runtime import DestructibleWorld
from destructible_impact_runtime import deliver
from effect_runtime import state,pool
from impact_specs import ActorHandle,Impact,HitFamily,HitOutcome
from portable_specs import LIMITS as L
from test_target_counter_runtime import manager,NAMES
suite=types.SimpleNamespace(INPUT=102584)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
world=load('dc_world','research/verify-destructible-world-short.py')
literal=load('dc_literal','research/verify-world-target-counters.py')
cross=world.cross
def bits(x):return struct.pack('<d',float(x)).hex()
def compile_case(c):
 w,meta=literal.compile_case(dict(name=c['name'],effects=c['effects'],actions=[(0,('activate',))]))
 # Results-backed landing packets use the existing landing entry's ABI;
 # literal mode0 admission itself remains unchanged and fully validated.
 w[0]=L['COUNTER_LANDING_ABI']
 extra=world.compile_case(c)
 for i,op in enumerate(c['ops']):
  if op[0]==1:extra[3872+i*32+12:3872+i*32+15]=[c.get('who',[2]*len(c['ops']))[i],c.get('family',1),i]
 return w+extra
def prepare():
 rows=[(c['name'],compile_case(c),c) for c in fixtures()];seed=rows[0][1];base=97464+3872+32
 for name,offset,value in [('attacker',12,5),('family',13,4),('attack-id',14,1<<24),('reserved',15,1)]:
  w=list(seed);w[base+offset]=value;rows.append(('reject/destructible-counter/'+name,w,None))
 w=list(seed);w[0]=L['TARGET_COUNTER_ABI'];rows.append(('reject/destructible-counter/literal-ABI-for-landing',w,None))
 packed=array.array('I',[len(rows)])
 for _,w,_ in rows:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 return rows,packed.tobytes()
def trace_normal(row):
 row=copy.deepcopy(row);row.pop('uid',None);row.pop('uid_ordinal',None)
 for k in ('credit','time'):row[k]=bits(row[k])
 if row['impact'] is not None:
  for k in ('damage','credit'):row['impact'][k]=bits(row['impact'][k])
 return row
def native_reference(c):
 expected_world=world.native_reference(c);w=DestructibleWorld(c['nodes'],c['bindings']);bm=manager(c['effects']);bm.notify('battle_start',0,NAMES[0]);steps=[]
 for i,(op,slot,kind,identity,generation,t,amount,credit,policy) in enumerate(c['ops']):
  if op==3:w.finish(t)
  else:w.advance(t)
  bm.tick(t)
  if op==1:
   who=c.get('who',[2]*len(c['ops']))[i]
   deliver(w,bm,slot,Impact(NAMES[who],ActorHandle(kind,identity,generation),c.get('family',1),policy,float(amount),float(credit),i))
  elif op==4:bm.notify('on_attack',t,NAMES[0])
  assert world.old.snapshot(w.targets)==expected_world['operations'][i]['state']
  records=[r for r in pool(bm,'target_hit_counter').values() if any(ab is r.carrier for ab in bm._active)]
  steps.append(dict(live=len(records),credit=bits(sum(r.credit for r in records)),completed=state(bm).counter_completed,epoch=state(bm).counter_epoch,dead=len(state(bm).dead_actors),resources=sorted([[r.epoch,bits(r.credit)] for r in records]),atk=bits(bm.get_buffs(NAMES[0],'__enemy__',t).get('atk_pct',0))))
  assert not state(bm).event_stack and not state(bm).impact_stack
 trace=[trace_normal(dict(dataclasses.asdict(record),time=t)) for t,record in state(bm).counter_trace]
 return dict(world=expected_world,counters=steps,trace=trace)
def decode(block,c):
 assert block[0]==0,(c['name'],block[0])
 side=block[600000:];side=array.array('I',side);side.extend([0]*(786432-len(side)))
 observed_world=world.decode(side,c);steps=[]
 def number(at):return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 for i,_ in enumerate(c['ops']):
  at=L['TARGET_COUNTER_QUERY_BASE']+i*16;count=block[at];assert count<=2
  steps.append(dict(live=count,credit=bits(number(at+1)),completed=block[at+3],epoch=block[at+4],dead=block[at+5],resources=sorted([[block[at+9+j*4],bits(number(at+10+j*4))] for j in range(count)]),atk=bits(number(620000+i*2640+24))))
 case=dict(c,actions=[None]*len(c['ops']))
 trace=[trace_normal(row) for row in literal.decoded(block,case)['completions']]
 return dict(world=observed_world,counters=steps,trace=trace)
def compare(block,c):
 expected=native_reference(c);actual=decode(block,c)
 assert actual==expected,(c['name'],actual,expected)
 return expected
def validate_rejection(block,name):assert name.startswith('reject/destructible-counter/') and block[0]==64,(name,block[:4])
