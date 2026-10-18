"""Independent state-recipient and filtered-rank CPU/GPU checks."""
import copy,hashlib,importlib.util,json,math,sys
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import run,compile_effects
from gpu_selector import Cuda
from detail_coverage import body_for,coverage
spec=importlib.util.spec_from_file_location('target_time_oracle',ROOT/'scripts/verify-time-detail.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
oracle=base.oracle;periodic=base.periodic;E=base.E;NAMES=periodic.NAMES

def primitives():
 out=[]
 def build(name,effects,commands,expected,chars=None):
  chars=chars or oracle.characters(NAMES);p=oracle.program(chars,[(e,NAMES[i]) for i,e in effects]);script=[[0,0,0,i,0,-1,0,0] for i in range(5)];qi=0
  for t,op,who in commands:
   if op=='query':script.append([t,2,0,who,-1,qi,0,0]);qi+=1
   else:script.append([t,0,op,who,0,-1,0,0])
  out.append((name,p,script,expected))
 queries=lambda t:[(t,'query',i) for i in range(5)]
 state=lambda **kw:E('mark','buff','',0,NAMES[3],**kw)
 withbuff=lambda **kw:E('selected','buff','atk_pct',7,'allies_with_buff:mark',**kw)
 without=lambda **kw:E('unselected','buff','atk_pct',13,'allies_without_buff:mark',**kw)
 build('state-membership-snapshot-and-complement',[(0,state()),(0,withbuff()),(0,without())],queries(.1),[13,13,13,7,13])
 build('unresolved-state-is-not-forced-by-membership',[(0,E('mark','buff','',0,'allies_top_atk:1')),(0,withbuff()),(0,without())],queries(.1),[13]*5)
 build('membership-does-not-follow-later-removal',[(0,state()),(0,withbuff()),(0,E('remove','instant','remove_named_buff',0,event='burst_cast',target_effect='mark'))],[(.2,3,0)]+queries(.3),[0,0,0,7,0])
 build('membership-reselected-on-reapplication',[(0,state()),(0,withbuff(event='on_attack',duration=.1)),(0,E('remove','instant','remove_named_buff',0,event='burst_cast',target_effect='mark'))],[(.1,7,0)]+queries(.15)+[(.2,3,0),(.3,7,0)]+queries(.4),[0,0,0,7,0]+[0]*5)
 build('zero-stack-state-is-still-a-recipient',[(0,E('mark','buff','',0,NAMES[3],polarity='harmful')),(0,E('zero','instant','debuff_stack_remove',1,NAMES[3],event='burst_cast',target_effect='mark')),(0,withbuff(event='on_attack'))],[(.1,3,0),(.2,7,0)]+queries(.3),[0,0,0,7,0])
 build('expired-state-excluded-after-expiry-pass',[(0,state(duration=.1)),(0,withbuff(event='on_attack'))],[(.2,7,0)]+queries(.3),[0]*5)
 build('same-frame-zero-duration-state-still-counts',[(0,state(duration=0)),(0,withbuff())],queries(.1),[0,0,0,7,0])
 build('empty-state-name-matches-empty-weapon-mode',[(0,E('empty state','buff','atk_pct',7,'allies_with_buff:'))],queries(.1),[7]*5)
 build('missing-state-complement-selects-everyone',[(0,E('no mark','buff','atk_pct',7,'allies_without_buff:missing'))],queries(.1),[7]*5)
 build('weapon-rank-uses-matching-pool-and-live-atk',[(1,E('strong','buff','atk_pct',100)),(0,E('rank','buff','atk_pct',7,'allies_weapon_top_atk:MG:1'))],queries(.1),[0,107,0,0,0])
 build('weapon-rank-empty-pool-is-empty',[(0,E('rank','buff','atk_pct',7,'allies_weapon_top_atk:SG:2'))],queries(.1),[0]*5)
 build('different-weapon-ranks-have-independent-cache-keys',[(0,E('mg','buff','atk_pct',7,'allies_weapon_top_atk:MG:1')),(0,E('sr','buff','atk_pct',13,'allies_weapon_top_atk:SR:1'))],queries(.1),[0,0,13,7,0])
 build('lowest-atk-innate-b3-uses-live-atk',[(2,E('alice stronger','buff','atk_pct',100)),(0,E('rank','buff','atk_pct',7,'allies_lowest_atk_burst3:1'))],queries(.1),[0,0,100,7,0])
 chars=oracle.characters(NAMES);chars[0]['burst_stage']='3'
 build('lowest-atk-b3-honors-pinned-innate-stage',[(0,E('rank','buff','atk_pct',7,'allies_lowest_atk_burst3:1'))],queries(.1),[7,0,0,0,0],chars)
 build('filtered-rank-hp-postprocessing-stays-lazy',[(0,E('lazy hp','buff','max_hp_pct',100,'allies_weapon_top_atk:MG:1'))],queries(.1),[0]*5)
 # Weapon modes are tracked independently of normal active buffs.
 from calculator.buff_manager import char_effects
 mode=copy.deepcopy(next(e for e in char_effects(NAMES[3]) if e['type']=='weapon_change'));mode['trigger']={'timing':['burst_cast'],'condition':[]};mode['duration']=.5
 build('generic-weapon-state-and-named-mode-expiry',[(3,mode),(0,E('generic','buff','atk_pct',7,'allies_with_buff:무기 변경',event='on_attack',duration=.1)),(0,E('named','buff','atk_pct',13,'allies_with_buff:'+mode['name'],event='on_attack',duration=.1))],[(.1,3,3),(.2,7,0)]+queries(.21)+[(.7,7,0)]+queries(.71),[0,0,0,20,0]+[0]*5)
 return out

def full_scenarios():
 n=NAMES
 yield 'full-state-snapshot-remove-and-recreate',{n[0]:[E('mark','buff','',0,n[3],event='every:2s',duration=1),E('selected','buff','atk_pct',30,'allies_with_buff:mark',event='every:0.5s',duration=3,max_stack=4),E('other','buff','crit_dmg',20,'allies_without_buff:mark',event='burst_cast',duration=8)]},12
 yield 'full-state-selected-heals-emit-recipient-events',{n[0]:[E('hp room','buff','max_hp_only_pct',100,'all_allies'),E('mark','buff','',0,n[3]),E('heal','instant','heal_hp_pct',1,'allies_with_buff:mark',event='every:1s',scaling='max_hp')],n[3]:[E('heal witness','buff','atk_pct',5,event='event:heal_received',max_stack=10)]},8
 yield 'full-filtered-weapon-rank-bullets',{n[0]:[E('rank bullets','buff','atk_pct',50,'allies_weapon_top_atk:MG:1',event='on_attack_count:2',duration_bullets=3),E('sr','buff','crit_dmg',20,'allies_weapon_top_atk:SR:1',event='burst_cast',duration=8)]},10
 yield 'full-lowest-b3-rank-refresh',{n[0]:[E('lowest','buff','atk_pct',30,'allies_lowest_atk_burst3:1',event='every:2s',duration=3,max_stack=3)]},12
 yield 'full-casted-weapon-recipient-masks',{n[0]:[E('mg cast','buff','atk_pct',30,'allies_burst_casted_weapon:MG',event='on_attack_count:3',duration=25,max_stack=3),E('sr cast','buff','crit_dmg',25,'allies_burst_casted_weapon:SR',event='full_burst_start',duration=25,max_stack=3)]},35
 from calculator.buff_manager import char_effects
 mode=copy.deepcopy(next(e for e in char_effects(n[3]) if e['type']=='weapon_change'))
 yield 'full-weapon-mode-membership',{n[3]:[mode],n[0]:[E('mode witness','buff','atk_pct',25,'allies_with_buff:무기 변경',event='every:0.5s',duration=1),E('outside mode','buff','crit_dmg',10,'allies_without_buff:무기 변경',event='every:0.5s',duration=1)]},25

def primitive_oracle(name,p,script,bs):
 from calculator.buff_manager import BuffManager
 original=BuffManager._resolve_target_raw;observations=[]
 def tracked(manager,target,caster):
  result=original(manager,target,caster)
  if isinstance(target,str) and target.startswith(('allies_with_buff:','allies_without_buff:')):
   observations.append({'target':target,'selected':list(result),'mark_states':[{'stack':ab.stack,'targets':ab.target_chars} for ab in manager._active if ab.effect.get('name')=='mark']})
  return result
 with patch.object(BuffManager,'_resolve_target_raw',tracked):cpu,totals=oracle.oracle(p,script,[31784,50],bs)
 if name=='zero-stack-state-is-still-a-recipient':assert any(ab['stack']==0 and ab['targets'] for o in observations for ab in o['mark_states']), 'zero-stack stimulus did not occur'
 if name=='unresolved-state-is-not-forced-by-membership':assert any(ab['targets'] is None for o in observations for ab in o['mark_states']), 'unresolved stimulus did not occur'
 return cpu,totals,observations

def verify(device,backend='auto',include_real=True):
 cases=[]
 for name,p,script,expected in primitives():
  bs={n:{'atk':100000+i*10000,'hp':1000000,'def':1000} for i,n in enumerate(NAMES)};cpu,totals,observations=primitive_oracle(name,p,script,bs);gpu=run(device,[p],script,[[31784,50]],[bs],module_backend=backend);errors=[]
  assert len(cpu)==len(expected)==len(gpu['queries'][0])
  for i,(x,y,z) in enumerate(zip(cpu,gpu['queries'][0],expected)):
   if x[0]!=z or y[0]!=z:errors.append([i,'expected atk',z,x[0],y[0]])
   for k in list(range(32))+[36,37]:
    if not math.isclose(x[k],y[k],rel_tol=1e-12,abs_tol=1e-8):errors.append([i,k,x[k],y[k]])
  case={'name':name,'passed':not errors and totals==gpu['totals'][0],'errors':errors,'backend':backend,'cpu_target_observations':observations};cases.append(case);print(json.dumps({k:x for k,x in case.items() if k!='cpu_target_observations'}),flush=True)
 for name,effects,seconds in full_scenarios():
  with periodic.custom_effects(effects):c=periodic.full.compare(device,name,body_for(NAMES,seconds,True),module_backend=backend)
  c['backend']=backend;cases.append(c);print(json.dumps({'name':name,'passed':c['passed'],'total':c['gpu_total']}),flush=True)
 if include_real:
  old=json.loads((ROOT/'research/detail-coverage-time.json').read_text(encoding='utf-8'));was={r['character'] for r in old['results'] if r['supported']};now=coverage()
  for r in now['results']:
   if not r['supported'] or r['character'] in was:continue
   name=r['character'];names=[name]+[n for n in NAMES if n!=name][:4];c=periodic.full.compare(device,'real-'+name,body_for(names,60,True),module_backend=backend);c['backend']=backend;cases.append(c);print(json.dumps({'name':name,'passed':c['passed'],'total':c['gpu_total']},ensure_ascii=True),flush=True)
 return cases

if __name__=='__main__':
 device=Cuda()
 try:cases=verify(device,'native')+verify(device,'ptx')
 finally:device.close()
 files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/verify-targets-detail.py']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'cases':cases,'cpu_trace_used_as_gpu_input':False,'scope':'authored state/filtered-rank cases and newly accepted fixed real squads; static boss, not all targets or combinations','source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 (ROOT/'research/detail-targets-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
