"""One physical state/trace comparison for CUDA and Metal, no CPU schedules."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from portable_effect_target_count_shot_specs import compile_case as pack,decode,INPUT
from portable_effect_target_count_shot_cases import fixtures as bases
from portable_heavyarms_lock_cases import source_definitions
from portable_specs import LIMITS as L,FIELDS as F
from effect_target_count_policy import MODEL
from portable_physical_lock_layout import OUTPUT,HEAD,PULSES,CANDIDATE,SNAPSHOTS,END,BASE,SET_WORDS
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
 for name,target,rebirth in [('full-charge-queued-kill','all_enemies',False),('full-charge-body-only','boss',False),('full-charge-queued-rebirth','all_enemies',True)]:
  c=copy.deepcopy(rows[0]);c['name']='physical-locks/'+name;c['patterns'][0]['spec']['hp']=1e8
  if rebirth:c['patterns'][0].update(after=['start','wave'],repeat=0,until=dict(targets_cleared=True))
  c['effects'].append(dict(name='full-charge-payload',source='스킬1',type='damage',stat='damage',fixed_value=1e8,target=target,trigger=dict(timing=['full_charge'],condition=[])))
  c['owners'].append(0);rows.append(c)
 return rows

def compile_case(c):
 words,meta,bindings=pack(parent,c,model=MODEL)
 pulse=next(i for i,name in enumerate(meta['effects']) if name=='록 온')
 meta['physical_lock_pulse_row']=pulse;return words,meta,bindings

def native_reference(domain):return observe(domain[0])

def compare(block,domain):
 c,m,bindings=domain;candidates=[];n=observe(c,candidate_observer=lambda values:candidates.append(tuple(values)))
 return compare_observed(block,domain,n,candidates)

def compare_observed(block,domain,n,candidates,*,manual=False,packet_bindings=False,pulse_rows=None,packet_rows=None,quota_rows=None):
 c,m,bindings=domain
 if block[0]!=0:raise AssertionError((c['name'],'status',block[0]))
 actual=parent.decoded(block,m,c,bindings);changed=[k for k in n['battle'] if k!='scope' and actual[k]!=n['battle'][k]]
 if changed:raise AssertionError((c['name'],'complete battle',changed))
 if parent.reload.charge.team.skill_trace(block,m)!=n['skill_trace']:raise AssertionError('Skill trace changed')
 if decode(block,m,trace_rows=quota_rows)!=n['target_count_shots']:raise AssertionError('Physical two-shot quota trace changed')
 h=HEAD;head=list(block[h:h+16]);want=[0x504c3031,len(n['lock_pulses']),len(n['lock_shots']),len(n['lock_clears']),0,m['physical_lock_pulse_row']]+[0]*10
 if head!=want:raise AssertionError(('lock header',head,want))
 if pulse_rows is not None and len(pulse_rows)!=len(n['lock_pulses']):raise AssertionError('Complete external pulse history required')
 for i,p in enumerate(n['lock_pulses']):
  at=PULSES+i*16;want=[*p['receipt'],*struct.unpack('<II',struct.pack('<d',p['time'])),*([0]*6)]
  actual=list(block[at:at+16]) if pulse_rows is None else pulse_rows[i]
  if actual!=want:raise AssertionError(('charge activation',i,actual,want))
 start=PULSES+(len(n['lock_pulses']) if pulse_rows is None else 0)*16
 if any(block[start:CANDIDATE]):raise AssertionError('Unexpected pulse tail')
 for i,shot in enumerate(n['lock_shots']):
  at=SNAPSHOTS+i*SET_WORDS;want=[0]*L['WORLD_ACTOR_SET_WORDS'];want[0]=len(shot['handles']);want[6]=0x474c3031;want[7]=shot['revision']
  for j,(kind,identity,generation) in enumerate(shot['handles']):
   slot=next(k for k,b in enumerate(bindings) if int(b.kind)==kind and b.identity==identity)
   want[1+slot//32]|=1<<(slot%32);want[8+j*4:12+j*4]=[slot,generation,kind,identity]
  if list(block[at:at+len(want)])!=want:raise AssertionError(('emission snapshot',i,list(block[at:at+16]),want[:16]))
 tail=SNAPSHOTS+len(n['lock_shots'])*SET_WORDS
 if manual or packet_bindings:
  from portable_physical_lock_cover_layout import BASE as manual_base,WORDS as manual_words
  if manual:
   manual_module=module('physical_manual_compare','research/verify-coordinate-manual-short.py')
   manual_module.compare_manual(block,n,base=manual_base)
  elif any(block[manual_base:manual_base+manual_words]):raise AssertionError('Unexpected manual posture')
  if any(block[tail:manual_base]):raise AssertionError('Unexpected lock snapshot padding')
  if packet_bindings:
   from portable_lock_packet_trace import compare as compare_packets
   compare_packets(block,n,m,trace_rows=packet_rows)
  elif any(block[manual_base+manual_words:OUTPUT]):raise AssertionError('Unexpected lock/manual padding')
 elif any(block[tail:OUTPUT]):raise AssertionError('Unexpected snapshot tail')
 want=[0]*SET_WORDS
 if candidates:
  want[0]=len(candidates[-1]);want[5]=1
  for i,handle in enumerate(candidates[-1]):
   slot=next(k for k,b in enumerate(bindings) if int(b.kind)==int(handle.kind) and b.identity==handle.identity)
   want[1+slot//32]|=1<<(slot%32);want[8+i*4:12+i*4]=[slot,handle.generation,int(handle.kind),handle.identity]
 if list(block[CANDIDATE:CANDIDATE+SET_WORDS])!=want:raise AssertionError('Complete final provider candidate buffer differs')
 if any(block[L['WORLD_ACTOR_POOL_QUERY_BASE']:L['WORLD_ACTOR_POOL_QUERY_BASE']+64*16]):raise AssertionError('Actor query bank borrowed')
 if any(block[L['WORLD_ACTOR_RECEIPT_BASE']:L['WORLD_ACTOR_RECEIPT_BASE']+64*8]):raise AssertionError('Actor receipt bank borrowed')
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
