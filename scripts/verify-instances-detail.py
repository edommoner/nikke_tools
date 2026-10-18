"""Independent CPU/GPU tests of multiple live instances of one definition."""
import copy,hashlib,importlib.util,json,math,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import run
from gpu_selector import Cuda
from detail_coverage import body_for
spec=importlib.util.spec_from_file_location('instance_chains',ROOT/'scripts/verify-chains-detail.py');chain=importlib.util.module_from_spec(spec);spec.loader.exec_module(chain)
E=chain.E;NAMES=chain.NAMES;oracle=chain.oracle;periodic=chain.periodic

def primitives():
 out=[]
 def build(name,effects,events,checks):
  p=oracle.program(oracle.characters(NAMES),[(e,NAMES[owner]) for owner,e in effects]);script=[[0,0,0,i,0,-1,0,0] for i in range(5)]
  commands=[(t,0,event,owner,0) for t,event,owner in events]+[(t,2,0,owner,i) for i,(t,owner,atk,ref) in enumerate(checks)]
  for t,op,ev,owner,index in sorted(commands,key=lambda x:(x[0],x[1])):script.append([t,op,ev,owner,p['states']['state'] if op==2 else 0,index if op==2 else -1,0,0])
  out.append((name,p,script,checks))
 def source(**kw):return E('state','buff','atk_pct',10,'all_allies',event='on_attack',duration=2,max_stack=3,**kw)
 remove=E('remove self','instant','remove_named_buff',0,event='burst_cast',target_effect='state',remove_scope='target')
 events=[(0,7,0),(.1,7,0),(.2,3,0),(.3,7,0),(.4,7,0)]
 checks=[(.15,0,20,2),(.25,0,0,2),(.25,1,20,0),(.35,0,10,2),(.35,1,30,0),(.45,0,20,2),(.45,1,40,0),(2.11,0,20,2),(2.11,1,20,0),(2.41,0,0,0)]
 build('partial-old-and-full-new-expire-independently',[(0,source()),(0,remove)],events,checks)
 limited=source(max_trigger=3)
 build('definition-trigger-budget-shared-by-instances',[(0,limited),(0,remove)],events,[(.45,0,10,2),(.45,1,30,0),(2.11,0,10,1),(2.31,0,0,0)])
 counted=source();counted['trigger']['timing']=['on_attack_count:2']
 build('notification-counter-shared-by-instances',[(0,counted),(0,remove)],events,[(.15,0,10,1),(.35,0,0,1),(.45,0,10,1),(.45,1,20,0)])
 short=source();short['duration']=1
 recycle_events=events+[(1.12,3,0),(1.2,7,0)]
 build('reused-primary-slot-appends-after-older-secondary',[(0,short),(0,remove)],recycle_events,[(1.11,0,20,2),(1.15,0,0,2),(1.21,0,10,2),(1.21,1,30,0),(1.41,0,10,1),(1.41,1,10,0)])
 first=source();first['max_stack']=1
 second=E('state','buff','atk_pct',20,'all_allies',event='hit_count:1',duration=5)
 build('cross-definition-name-merge-matches-targets',[(0,first),(0,second),(0,remove)],[(0,7,0),(.1,3,0),(.2,8,0),(.4,7,0)],[(.3,0,20,1),(.3,1,30,0),(2.01,1,20,0),(2.41,0,0,0)])
 # Scope removal retains a shield creation map for surviving partial instances.
 shield=E('state','buff','shield_from_max_hp_pct',50,'all_allies',event='on_attack',duration=2)
 watcher=E('shield witness','buff','atk_pct',25,event='passive',condition=['during_shield'])
 build('shield-post-uses-first-live-same-effect-instance',[(0,shield),(0,remove),(0,watcher)],[(0,7,0),(.1,3,0),(.2,7,0)],[(.05,0,25,1),(.15,0,25,1),(.25,0,0,1),(.25,1,0,0)])
 periodic_source=source();periodic_source['trigger']['timing']=['every:0.5s']
 build('periodic-clock-is-shared-by-instances',[(0,periodic_source),(0,remove)],[(.6,3,0)],[(.51,0,10,1),(.61,0,0,1),(1.01,0,10,1),(1.01,1,20,0),(1.51,0,20,1),(1.51,1,30,0)])
 bullet=source();bullet['duration_bullets']=3
 build('bullet-bound-reapplication-restores-one-instance',[(0,bullet),(0,remove)],[(0,7,0),(.1,3,0),(.2,7,0)],[(.05,0,10,1),(.15,0,0,1),(.25,0,20,2),(.25,1,20,0)])
 return out

def full_scenarios():
 n=periodic.NAMES
 source=E('state','buff','atk_pct',11,'all_allies',event='on_attack_count:3',duration=1.1,max_stack=4,max_trigger=23)
 remove=E('scope','instant','remove_named_buff',0,event='every:0.35s',target_effect='state',remove_scope='target')
 yield 'full-shared-budget-counts-and-overlap',{n[0]:[source],n[1]:[remove]},8
 yield 'full-partial-shields-and-health-posts',{n[0]:[E('state','buff','max_hp_pct',10,'all_allies',event='on_attack_count:3',duration=1.1,max_stack=4),E('shield','buff','shield_from_max_hp_pct',10,'all_allies',event='on_attack_count:4',duration=1.2)],n[1]:[remove,E('shield scope','instant','remove_named_buff',0,event='every:0.45s',target_effect='shield',remove_scope='target'),E('shield attack','buff','atk_pct',30,event='passive',condition=['during_shield'])]},8
 # Nested notification removes/recreates while parent activation posts are pending.
 src=E('state','buff','atk_pct',11,'all_allies',event='on_attack_count:3',duration=1.2,max_stack=3)
 nested=E('nested removal','instant','remove_named_buff',0,event='event:state',target_effect='state',remove_scope='target',max_trigger=5)
 src['trigger']['timing'].append('event:state_end:state')
 yield 'full-nested-partial-removal-reapplication',{n[0]:[src,nested],n[1]:[remove]},8
 yield 'full-quantized-ammo-and-charge-speed-overlap',{n[2]:[E('state','buff','max_ammo_pct',32.12,'all_allies',event='full_charge_fire',duration=2.5,max_stack=4),E('charge state','buff','charge_speed_pct',20.3,'all_allies',event='full_charge_fire',duration=2.5,max_stack=4)],n[0]:[E('ammo scope','instant','remove_named_buff',0,n[2],event='every:0.35s',target_effect='state',remove_scope='target'),E('charge scope','instant','remove_named_buff',0,n[2],event='every:0.4s',target_effect='charge state',remove_scope='target')]},16

def verify(device,backend='auto'):
 cases=[]
 for name,p,script,checks in primitives():
  bs={n:{'atk':100000+i*10000,'hp':1000000,'def':1000} for i,n in enumerate(NAMES)}
  cpu,totals=oracle.oracle(p,script,[31784,50],bs);gpu=run(device,[p],script,[[31784,50]],[bs],module_backend=backend);errors=[]
  for i,(x,y,check) in enumerate(zip(cpu,gpu['queries'][0],checks)):
   for key,expected in [(0,check[2]),(37,check[3])]:
    if x[key]!=expected or y[key]!=expected:errors.append([i,key,expected,x[key],y[key]])
   for k in list(range(32))+[36,37]:
    if not math.isclose(x[k],y[k],rel_tol=1e-12,abs_tol=1e-8):errors.append([i,k,x[k],y[k]])
  case={'name':name,'passed':not errors and totals==gpu['totals'][0],'errors':errors,'backend':backend};cases.append(case);print(json.dumps(case),flush=True)
 for name,effects,seconds in full_scenarios():
  from calculator.buff_manager import BuffManager
  from unittest.mock import patch
  from collections import Counter
  activate=BuffManager._activate;peak=[0]
  def witnessed(manager,*args,**kw):
   result=activate(manager,*args,**kw)
   peak[0]=max(peak[0],max(Counter(id(ab.effect) for ab in manager._active).values(),default=0))
   return result
  with periodic.custom_effects(effects),patch.object(BuffManager,'_activate',witnessed):case=periodic.full.compare(device,name,body_for(periodic.NAMES,seconds,True),module_backend=backend)
  case['cpu_peak_instances_of_one_effect']=peak[0];case['passed'] &= peak[0]>1
  case['backend']=backend;cases.append(case);print(json.dumps({'name':name,'passed':case['passed'],'cpu':case['cpu_total'],'gpu':case['gpu_total']},ensure_ascii=True),flush=True)
 return cases

if __name__=='__main__':
 d=Cuda()
 try:cases=verify(d,'native')+verify(d,'ptx')
 finally:d.close()
 files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/verify-instances-detail.py']
 r={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 (ROOT/'research/detail-instances-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
