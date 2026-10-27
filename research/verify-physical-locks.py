"""One physical state/trace comparison for CUDA and Metal, no CPU schedules."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from portable_effect_target_count_shot_specs import compile_case as pack,decode,INPUT,OUTPUT
from portable_effect_target_count_shot_cases import fixtures as bases
from portable_heavyarms_lock_cases import source_definitions
from portable_specs import LIMITS as L,FIELDS as F
from effect_target_count_policy import MODEL
from world_physical_locks_native import observe

def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
parent=module('physical_lock_parent','research/verify-world-projectile.py');cross=module('physical_lock_digest','research/summarize-portable-cross-gpu.py')
SOURCE='gpu/world_physical_locks_entry.slang';suite=SimpleNamespace(SOURCE=SOURCE,INPUT=INPUT,OUTPUT=OUTPUT)

def fixtures():
 rows=[]
 for name,charge,hp in [('charge-two-shot-quota',.45,1e15),('charge-live-death',.45,10000),('short-charge-grid',.1,1e15)]:
  c=copy.deepcopy(bases()[1]);c.update(name='physical-locks/'+name,duration=1.8,lock_owner=0)
  pulse=dict(copy.deepcopy(source_definitions()[0]),stat='',target='self')
  c['effects'].append(pulse);c['owners'].append(0)
  c['patterns']=[dict(id='wave',kind='summon',spec=dict(count=16,hp=hp))]
  w=c['combat']['weapons'][0];w.update(charge=charge,interval=charge+.215,min_cycle=charge+.215)
  rows.append(c)
 return rows

def compile_case(c):
 words,meta,bindings=pack(parent,c,model=MODEL)
 pulse=next(i for i,name in enumerate(meta['effects']) if name=='록 온')
 meta['physical_lock_pulse_row']=pulse;return words,meta,bindings

def native_reference(domain):return observe(domain[0])

def compare(block,domain):
 c,m,bindings=domain;n=observe(c)
 if block[0]!=0:raise AssertionError((c['name'],'status',block[0]))
 actual=parent.decoded(block,m,c,bindings);changed=[k for k in n['battle'] if k!='scope' and actual[k]!=n['battle'][k]]
 if changed:raise AssertionError((c['name'],'complete battle',changed))
 if parent.reload.charge.team.skill_trace(block,m)!=n['skill_trace']:raise AssertionError('Skill trace changed')
 if decode(block,m)!=n['target_count_shots']:raise AssertionError('Physical two-shot quota trace changed')
 h=L['WORLD_ACTOR_POOL_QUERY_BASE']+63*16;head=list(block[h:h+16]);want=[0x504c3031,len(n['lock_pulses']),len(n['lock_shots']),len(n['lock_clears']),0,m['physical_lock_pulse_row']]+[0]*10
 if head!=want:raise AssertionError(('lock header',head,want))
 for i,p in enumerate(n['lock_pulses']):
  at=L['WORLD_ACTOR_POOL_QUERY_BASE']+i*16;want=[*p['receipt'],*struct.unpack('<II',struct.pack('<d',p['time'])),*([0]*6)]
  if list(block[at:at+16])!=want:raise AssertionError(('charge activation',i,list(block[at:at+16]),want))
  at=L['WORLD_ACTOR_RECEIPT_BASE']+i*8
  if list(block[at:at+8])!=p['receipt']:raise AssertionError('Pulse receipt changed')
 start=L['WORLD_ACTOR_POOL_QUERY_BASE']+len(n['lock_pulses'])*16
 if any(block[start:h]):raise AssertionError('Unexpected pulse tail')
 for i,shot in enumerate(n['lock_shots']):
  at=L['WORLD_ACTOR_SET_BASE']+(i+1)*L['WORLD_ACTOR_SET_WORDS'];want=[0]*L['WORLD_ACTOR_SET_WORDS'];want[0]=len(shot['handles']);want[6]=0x474c3031;want[7]=shot['revision']
  for j,(kind,identity,generation) in enumerate(shot['handles']):
   slot=next(k for k,b in enumerate(bindings) if int(b.kind)==kind and b.identity==identity)
   want[1+slot//32]|=1<<(slot%32);want[8+j*4:12+j*4]=[slot,generation,kind,identity]
  if list(block[at:at+len(want)])!=want:raise AssertionError(('emission snapshot',i,list(block[at:at+16]),want[:16]))
 tail=L['WORLD_ACTOR_SET_BASE']+(len(n['lock_shots'])+1)*L['WORLD_ACTOR_SET_WORDS']
 if any(block[tail:L['WORLD_ACTOR_SET_BASE']+32*L['WORLD_ACTOR_SET_WORDS']]):raise AssertionError('Unexpected snapshot tail')
 if any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]):raise AssertionError('Counter context not restored')
 return n

def prepare():
 entries=[]
 for c in fixtures():
  w,m,b=compile_case(c);entries.append((c['name'],w,(c,m,b)))
 seed=entries[0][1];pulse=entries[0][2][1]['physical_lock_pulse_row'];at=L['DEFINITION_BASE']+pulse*L['DEFINITION_WORDS']
 for name,pos,value in [('pulse-kind',at+F['KIND'],0),('pulse-owner',at+F['OWNER'],1),('charge-condition',L['CONDITION_BASE']+pulse*L['CONDITION_WORDS'],0),('pulse-name',at+F['NAME'],255)]:
  w=list(seed);w[pos]=value;entries.append(('reject/'+name,w,None))
 data=array.array('I',[len(entries)])
 for _,w,_ in entries:data.extend(w)
 if sys.byteorder!='little':data.byteswap()
 return entries,data.tobytes()
