"""Actual world pools + shared named quotas; explicit provider order, no metric."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from portable_specs import LIMITS as L,FIELDS as F
from named_generation_locks import GenerationLocks,MODEL,registry_views
from effect_target_count_policy import query,MODEL as CAPACITY_MODEL
from test_target_counter_runtime import manager,NAMES
from portable_heavyarms_lock_cases import source_definitions
from impact_specs import ActorHandle

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
parent=module('generation_lock_pool','research/verify-world-actor-pools.py')
cross=module('generation_lock_digest','research/summarize-portable-cross-gpu.py')
SOURCE='gpu/world_generation_locks_entry.slang';MAGIC=0x474c3031
suite=SimpleNamespace(INPUT=L['WORLD_ACTOR_POOL_INPUT_WORDS'],OUTPUT=L['WORLD_ACTOR_POOL_OUTPUT_WORDS'],SOURCE=SOURCE)

def fixtures():
 base=parent.fixtures()[0];rows=[]
 def add(name,patterns,actions,duration=.5,who=0,marker='록 온'):
  c=copy.deepcopy(base);c.update(name='generation-locks/'+name,patterns=patterns,actions=actions,duration=duration,lock_who=who,lock_marker=marker)
  effect=copy.deepcopy(source_definitions()[20]);effect.update(stat='',duration=.3,duration_bullets=-1,trigger=dict(timing=['battle_start'],condition=[]))
  c['effects']=[effect];c['owners']=[0]
  for w in c['combat']['weapons']:w['enabled']=False
  rows.append(c);return c
 capture=lambda t,mask=33:(t,35,[mask,0,0,0,0],0)
 acquire=lambda t,index,base=5,limit=128:(t,45,[0,0,base,limit,index<<8],0)
 snap=lambda t,index,reason=0:(t,46,[index,reason,0,0,0],0)
 wave=lambda **kw:dict(id='wave',kind='summon',spec=dict(count=16,hp=3),**kw)
 # Battle start activates the derived time modifier in the real shared loop.
 add('distinct-five-plus-ten-and-capacity-drop',[wave()],[capture(0)]+[acquire(0,i) for i in range(16)]+[snap(.2,30),acquire(.31,16),snap(.31,31)])
 add('caster-isolation',[wave()],[capture(0)]+[acquire(0,i) for i in range(6)]+[snap(.1,31)],who=1)
 add('marker-isolation',[wave()],[capture(0)]+[acquire(0,i) for i in range(6)]+[snap(.1,31)],marker='other')
 for reason in (1,2):add('clear-'+str(reason),[wave()],[capture(0),acquire(0,0),snap(.1,30,reason),acquire(.1,1),snap(.1,31)])
 add('death-prunes-without-body-alias',[wave()],[capture(0,32),acquire(0,0),(0,34,[0,5,0,1,20],10),acquire(.1,1),snap(.1,31)])
 add('frozen-candidate-stale-generation',[wave(after=['start','wave'],repeat=0,until=dict(time=.1))],[capture(0,32),acquire(0,0),acquire(.25,1),snap(.25,30),(.25,38,[0,0,0,0,0],0),capture(.25,32),acquire(.25,2),snap(.25,31)])
 add('not-yet-born',[wave(delay=.2)],[capture(0,32),acquire(0,0),snap(.1,31)])
 add('typed-body-parts-adds',[dict(id='parts',kind='parts',targets=[dict(name='a',hp=3),dict(name='b',hp=3)]),wave()],[capture(0,35)]+[acquire(0,i) for i in range(8)]+[snap(.1,31)])
 p=wave();p['spec']['count']=127
 add('all-128-provider-rows',[p],[capture(0)]+[acquire(0,i,128) for i in range(24)]+[snap(.1,31)],marker='other')
 return rows

def compile_case(c):
 words,meta,bindings=parent.compile_case(c)
 if len(words)!=suite.INPUT:raise AssertionError('Pool wire changed')
 name=c['lock_marker'];names=meta['states']
 for symbol in (name,'록 온'):
  if symbol not in names:names[symbol]=len(names)
 row=L['DEFINITION_BASE'];words[row+F['STAT']]=93;words[row+F['TARGET_NAME']]=names['록 온']
 # The original modifier is explicitly derived to a finite external time window.
 for step in range(words[2]):
  at=L['COMMAND_BASE']+step*8
  if words[at]==45:words[at+3]=c['lock_who'];words[at+4]=names[name]
 return words,meta,bindings

def observe(c):
 bm=manager([dict(c['effects'][0],stat='effect_target_count_add')],[0]);bm.notify('battle_start',0,NAMES[0])
 core=GenerationLocks(capacity_limit=128,eligible_kinds=(0,1,5),model=MODEL);candidates={};receipts={};snapshots={}
 def observer(t,op,args,reg,boss):
  views=registry_views(reg);bm.tick(t)
  if op==35:
   mask,index,*_=args;live=[r for r in views if r.alive and mask&(1<<int(r.handle.kind))]
   def order(r):
    if r.handle.kind==5:
     b=next(b for b in __import__('world_actor_pool_native').actor_bindings(boss) if int(b.kind)==5 and b.identity==r.handle.identity)
     return (5,boss._runs[b.run].adds[b.slot].order)
    return (int(r.handle.kind),r.handle.identity)
   candidates[index]=[r.handle for r in sorted(live,key=order)]
  elif op==45:
   _,_,base,limit,packed=args
   cap=query(bm,NAMES[c['lock_who']],c['lock_marker'],t,base_count=base,capacity_limit=limit,model=CAPACITY_MODEL)['capacity']
   answer=core.acquire(views,candidates[packed&255],capacity=cap);h=answer.selected
   receipts[packed>>8]=[cap,len(answer.snapshot.handles),answer.snapshot.revision,int(h.kind) if h else 0xffffffff,h.identity if h else 0,h.generation if h else 0,len(answer.removed),MAGIC]
  elif op==46:
   index,reason,*_=args;core.sync(views);snapshots[index]=core.snapshot()
   if reason:core.clear({1:'normal_attack',2:'taking_cover'}[reason])
 pools=parent.manual.native(c,L,action_observer=observer)
 # Existing pool battle output remains independently compared in full.
 return dict(pool=pools,receipts=receipts,snapshots={i:dict(revision=s.revision,handles=[[int(h.kind),h.identity,h.generation] for h in s.handles]) for i,s in snapshots.items()})

def native_reference(domain):return observe(domain[0])

def compare(block,domain):
 c,meta,bindings=domain;expected=observe(c)
 if block[0]!=0:raise AssertionError((c['name'],'GPU status',block[0]))
 actual=parent.manual.decoded(block,c,L,bindings)
 if actual!=expected['pool']:raise AssertionError((c['name'],'world pool differs',actual,expected['pool']))
 for index,row in expected['receipts'].items():
  at=L['WORLD_ACTOR_RECEIPT_BASE']+index*8
  if list(block[at:at+8])!=row:raise AssertionError((c['name'],'lock receipt',index,list(block[at:at+8]),row))
 for index,row in expected['snapshots'].items():
  at=L['WORLD_ACTOR_SET_BASE']+index*L['WORLD_ACTOR_SET_WORDS'];raw=list(block[at:at+L['WORLD_ACTOR_SET_WORDS']]);want=[0]*len(raw)
  want[0]=len(row['handles']);want[6]=MAGIC;want[7]=row['revision']
  for i,(kind,identity,generation) in enumerate(row['handles']):
   slot=next(j for j,b in enumerate(bindings) if int(b.kind)==kind and b.identity==identity)
   want[1+slot//32]|=1<<(slot%32);want[8+i*4:12+i*4]=[slot,generation,kind,identity]
  if raw!=want:raise AssertionError((c['name'],'immutable snapshot',index,raw[:16],want[:16]))
 return expected

def prepare():
 entries=[]
 for c in fixtures():
  w,m,b=compile_case(c);entries.append((c['name'],w,(c,m,b)))
 seed=entries[0][1];acq=next(i for i in range(seed[2]) if seed[L['COMMAND_BASE']+i*8]==45);at=L['COMMAND_BASE']+acq*8
 for name,pos,value in [('who',at+3,5),('marker',at+4,256),('limit',at+6,129),('unowned-provider',at+7,1),('receipt',at+7,64<<8),('base-over-limit',at+5,129)]:
  w=list(seed);w[pos]=value;entries.append(('reject/'+name,w,None))
 data=array.array('I',[len(entries)])
 for _,words,_ in entries:data.extend(words)
 if sys.byteorder!='little':data.byteswap()
 return entries,data.tobytes()
