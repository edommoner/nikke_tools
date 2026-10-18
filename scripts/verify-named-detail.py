"""Named state removal/extension: independent CPU state and full combat oracles."""
import copy,hashlib,importlib.util,json,math,sys
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import run
from gpu_selector import Cuda
from detail_coverage import a,body_for

def load(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
oracle=load('named_state_oracle','verify-detail.py');periodic=load('named_full_oracle','verify-periodic-detail.py')
effect=periodic.effect
NAMES=['모더니아','루주','마스트 : 로망틱 메이드','도라','얀']

def primitives():
 cases=[]
 def build(name,effects,commands,expected):
  chars=oracle.characters(NAMES);program=oracle.program(chars,[(e,NAMES[who]) for who,es in effects.items() for e in es]);script=[[0,0,0,i,0,-1,0,0] for i in range(5)];qi=0
  for t,op,who in commands:
   if op=='query':script.append([t,2,0,who,-1,qi,0,0]);qi+=1
   else:script.append([t,0,op,who,0,-1,0,0])
  cases.append((name,program,script,expected))
 buff=lambda name,value,target='self',**kw:effect(name,'buff','atk_pct',value,target,**kw)
 remove=lambda name,target='self',**kw:effect('remove '+name,'instant','remove_named_buff',0,target,event='burst_cast',target_effect=name,**kw)
 extend=lambda name,target='self',value=1,**kw:effect('extend '+name,'instant','named_buff_duration_extend',value,target,event='burst_cast',target_effect=name,**kw)
 build('global-removal-across-casters',{0:[remove('shared','all_allies')],1:[buff('shared',10)],2:[buff('shared',20)]},[(.1,'query',1),(.1,'query',2),(1,3,0),(1,'query',1),(1,'query',2)],[10,20,0,0])
 build('empty-state-name-removal-has-no-end-notification',{0:[buff('',10),remove(''),effect('must not fire','buff','atk_pct',99,event='event:state_end:')]},[(1,3,0),(1,'query',0)],[0])
 build('empty-state-name-scoped-removal-cpu-exception',{0:[buff('',10),remove('',remove_scope='target'),effect('must fire','buff','atk_pct',99,event='event:state_end:')]},[(1,3,0),(1,'query',0)],[99])
 build('empty-state-name-expiry-has-no-end-notification',{0:[buff('',10,duration=.5),effect('must not fire','buff','atk_pct',99,event='event:state_end:')]},[(1,'query',0)],[0])
 build('scope-retains-other-recipients',{0:[buff('shared',10,'all_allies'),remove('shared',remove_scope='target')]},[(.1,'query',0),(1,3,0),(1,'query',0),(1,'query',1)],[10,0,10])
 build('scope-same-name-different-casters',{0:[remove('shared',NAMES[1],remove_scope='target')],1:[buff('shared',10)],2:[buff('shared',20)]},[(1,3,0),(1,'query',1),(1,'query',2)],[0,20])
 build('scope-does-not-resolve-lazy-state',{0:[buff('lazy',10,'allies_top_atk:1'),remove('lazy',remove_scope='target')]},[(.1,3,0),(.1,'query',4)],[10])
 for limited in (False,True):
  build('empty-target-global-removal-limited-'+str(limited),{0:[buff('shared',10),remove('shared','N102',**({'max_trigger':1} if limited else {}))]},[(1,3,0),(1,'query',0)],[10 if limited else 0])
 build('missing-state-removal-is-no-op',{0:[buff('existing',10),remove('unregistered','all_allies')]},[(1,3,0),(1,'query',0)],[10])
 build('extension-prefix-boundary',{0:[buff('mode',10,duration=1),buff('mode 2',20,duration=1),buff('mode2',40,duration=1),extend('mode')]},[(.5,3,0),(1.1,'query',0),(2,'query',0)],[30,0])
 high=[effect('filler '+str(i),'buff','crit_dmg',0) for i in range(98)]+[buff('mode',10,duration=1),buff('mode 2',20,duration=1),buff('mode2',40,duration=1),extend('mode')]
 build('extension-high-state-id-bitwords',{0:high},[(.5,3,0),(1.1,'query',0)],[30])
 build('extension-needs-recipient-intersection',{0:[buff('mode',10,NAMES[1],duration=1),extend('mode')]},[(.5,3,0),(1.1,'query',1)],[0])
 build('extension-infinite-and-unresolved-lazy',{0:[buff('mode',10),buff('mode 2',20,'allies_top_atk:1',duration=1),extend('mode','all_allies')]},[(.5,3,0),(1.1,'query',0),(1.1,'query',4)],[10,0])
 return cases

def full_scenarios():
 n=periodic.NAMES
 E=effect
 cases=[]
 es={n[0]:[E('shared','buff','atk_pct',80,'all_allies',duration=10),E('remove shared','instant','remove_named_buff',0,'self',event='burst_cast',target_effect='shared',remove_scope='target'),E('shared ended','buff','crit_dmg',30,event='event:state_end:shared',max_stack=10)],n[2]:[E('remove remaining','instant','remove_named_buff',0,'all_allies',event='burst_cast',target_effect='shared',remove_scope='target')]}
 cases.append(('partial-removal-then-final-end',es,12))
 es={n[0]:[E('shield','buff','shield_from_max_hp_pct',40,'all_allies',duration=10),E('remove shield','instant','remove_named_buff',0,event='burst_cast',target_effect='shield',remove_scope='target'),E('shield damage','buff','atk_pct',50,condition=['during_shield'])],n[2]:[E('other shield predicate','buff','atk_pct',75,condition=['during_shield'])]}
 cases.append(('scoped-removal-retains-cpu-shield-map',es,8))
 es={n[0]:[E('shots','buff','atk_pct',80,'all_allies',duration_bullets=200),E('remove shots','instant','remove_named_buff',0,event='burst_cast',target_effect='shots',remove_scope='target')]}
 cases.append(('scoped-bullet-buff-retains-other-counters',es,10))
 es={n[0]:[E('dot','damage','dot_damage',100,'target',tick_interval=.5,duration=1),E('extend dot','instant','named_buff_duration_extend',2,'target',event='every:0.5s',max_trigger=1,target_effect='dot')]}
 cases.append(('extension-updates-real-dot-timer',es,5))
 es={n[0]:[E('cancelled dot','damage','dot_damage',100,'target',tick_interval=.5,duration=10),E('cancel','instant','remove_named_buff',0,'target',event='burst_cast',target_effect='cancelled dot',remove_scope='target'),E('ended','buff','atk_pct',30,event='event:state_end:cancelled dot')]}
 cases.append(('scoped-enemy-dot-cancels-timer',es,8))
 es={n[0]:[E('shared','buff','atk_pct',50),E('remove all','instant','remove_named_buff',0,'all_allies',event='burst_cast',target_effect='shared'),E('recreate after removal','buff','crit_dmg',15,event='event:state_end:shared')],n[2]:[E('shared','buff','charge_dmg_pct',100),E('end adds damage','damage','damage',100,'target',event='event:state_end:shared')]}
 cases.append(('global-removal-cross-caster-end-chain',es,8))
 es={n[0]:[E('shots','buff','atk_pct',80,'all_allies',duration_bullets=5),E('remove slow recipient','instant','remove_named_buff',0,n[2],target_effect='shots',remove_scope='target'),E('reference stays until all bullet counters finish','buff','atk_dmg_pct',100,scaling='stack_count',scaling_ref='shots'),E('last counter notification','damage','damage',100,'target',event='event:state_end:shots')]}
 cases.append(('scoped-bullet-lifetime-includes-removed-recipient',es,12))
 return cases

def verify(device,backend='auto'):
 results=[]
 for name,program,script,expected in primitives():
  bs={n:{'atk':100000+i*10000,'hp':1000000,'def':1000} for i,n in enumerate(NAMES)}
  cpu,totals=oracle.oracle(program,script,[31784,50],bs);gpu=run(device,[program],script,[[31784,50]],[bs],module_backend=backend)
  errors=[]
  for i,(x,y) in enumerate(zip(cpu,gpu['queries'][0])):
   if x[0]!=expected[i] or y[0]!=expected[i]:errors.append([i,'expected atk',expected[i],x[0],y[0]])
   for k in (0,6,28,37):
    if not math.isclose(x[k],y[k],rel_tol=1e-12,abs_tol=1e-8):errors.append([i,k,x[k],y[k]])
  case={'name':name,'passed':not errors,'errors':errors,'backend':gpu['module_backend']};results.append(case);print(json.dumps(case),flush=True)
 for name,effects,seconds in full_scenarios():
  from calculator.buff_manager import BuffManager
  dispatch=BuffManager._dispatch_instant;actions={'named_operations_changed':0}
  def track_operation(manager,eff,caster,t,**kw):
   watched=eff.get('stat') in ('remove_named_buff','named_buff_duration_extend')
   def snapshot():return [(ab.uid,tuple(ab.target_chars or []),ab.expires_at) for ab in manager._active]
   before=snapshot() if watched else None;result=dispatch(manager,eff,caster,t,**kw)
   if watched and before!=snapshot():actions['named_operations_changed']+=1
   return result
  with periodic.custom_effects(effects) as observed,patch.object(BuffManager,'_dispatch_instant',track_operation):
   case=periodic.full.compare(device,name,body_for(periodic.NAMES,seconds),module_backend=backend)
  observed.update(actions);case['passed'] &= actions['named_operations_changed']>0
  case['observed']=copy.deepcopy(observed);case['backend']=backend
  if name=='extension-updates-real-dot-timer':case['passed'] &= observed['damage_ticks']==6
  if name=='scoped-enemy-dot-cancels-timer':case['passed'] &= observed['damage_ticks']==5
  results.append(case);print(json.dumps({'name':name,'passed':case['passed'],'cpu':case['cpu_total'],'gpu':case['gpu_total'],'ticks':observed['damage_ticks']}),flush=True)
 # Real newly accepted characters are exercised with their unmodified skills.
 old=json.loads((ROOT/'research/detail-coverage-after.json').read_text(encoding='utf-8'));new=json.loads((ROOT/'research/detail-coverage-named.json').read_text(encoding='utf-8'));was={r['character'] for r in old['results'] if r['supported']}
 for record in new['results']:
  name=record['character']
  if record['supported'] and name not in was:
   squad=[name]+[n for n in NAMES if n!=name][:4]
   from calculator.buff_manager import BuffManager
   dispatch=BuffManager._dispatch_instant;observed={'live_named_removals':0}
   def track(manager,eff,caster,t,**kw):
    if eff.get('stat')=='remove_named_buff' and any(ab.effect.get('name')==eff.get('target_effect') for ab in manager._active):observed['live_named_removals']+=1
    return dispatch(manager,eff,caster,t,**kw)
   with patch.object(BuffManager,'_dispatch_instant',track):case=periodic.full.compare(device,'real-'+name,body_for(squad,60,True),module_backend=backend)
   case['backend']=backend;case['observed']=observed;case['mechanic_scope']='Real squad damage parity; live removal itself is required by the synthetic full-squad cases above';results.append(case);print(json.dumps({'name':name,'passed':case['passed'],'cpu':case['cpu_total'],'gpu':case['gpu_total'],'observed':observed},ensure_ascii=True),flush=True)
 return results

if __name__=='__main__':
 d=Cuda()
 try:cases=verify(d,'native')+verify(d,'ptx')
 finally:d.close()
 sources=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/engine_worker.py','scripts/verify-named-detail.py']
 r={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}}
 (ROOT/'research/detail-named-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
