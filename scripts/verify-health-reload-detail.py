"""Independent HP-to-ATK, fixed reload, forced reload and whole-squad checks."""
import sys,json,copy,math,hashlib,importlib.util
from pathlib import Path
from datetime import datetime,timezone
from contextlib import contextmanager
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for,coverage
from detail_gpu import run,compile_effects
from gpu_selector import Cuda
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=load('health_reload_periodic','scripts/verify-periodic-detail.py');oracle=load('health_reload_oracle','scripts/verify-detail.py');modes=load('health_reload_modes','scripts/verify-modes-detail.py')
NAMES=p.NAMES;E=p.effect

def primitives():
 # Individual query outputs, independent of combat and shared base HP values.
 for label,es in [
  ('hp-conversion-each-recipient',[(E('hp conversion','buff','atk_from_hp_pct',3.14,'all_allies'),NAMES[0])]),
  ('hp-conversion-expiry-and-caster-order',[(E('caster flat','buff','atk_caster_based_pct',7,'all_allies'),NAMES[1]),(E('conversion','buff','atk_from_hp_pct',2.71,'all_allies'),NAMES[0]),(E('hp window','buff','max_hp_pct',23.45,'all_allies',duration=.5),NAMES[0])]),
  ('hp-conversion-rank-excludes-conversion',[(E('conversion','buff','atk_from_hp_pct',99),NAMES[0]),(E('ranking','buff','atk_pct',7,'allies_top_atk:1'),NAMES[2])]),
  ('hp-conversion-lazy-query-reselects',[(E('conversion','buff','atk_from_hp_pct',1,'allies_top_atk:1'),NAMES[0]),(E('rank changes','buff','atk_pct',500,event='burst_cast'),NAMES[1])]),
  ('hp-conversion-stacks',[(E('conversion','buff','atk_from_hp_pct',.7,'all_allies',event='on_attack',max_stack=5,duration=1),NAMES[0])]),
  ('hp-effective-max-ignores-runtime-gate',[(E('conversion','buff','atk_from_hp_pct',3),NAMES[0]),(E('conditional hp','buff','max_hp_pct',50,event='passive',condition=['during_full_burst']),NAMES[0])]),
  ('fixed-reload-max-not-latest',[(E('slow fixed','buff','reload_time_fixed',.9,'all_allies',duration=.5),NAMES[0]),(E('fast fixed','buff','reload_time_fixed',.2,'all_allies'),NAMES[0]),(E('speed ignored','buff','reload_speed_pct',99,'all_allies'),NAMES[0])]),
  ('fixed-reload-zero',[(E('zero','buff','reload_time_fixed',0,'all_allies'),NAMES[0])]),
  ('fixed-reload-missing-value-is-marker',[(dict(source='스킬1',name='marker only',type='buff',stat='reload_time_fixed',target='all_allies',trigger={'timing':['battle_start'],'condition':[]},duration=-1),NAMES[0])]),
  ('fixed-reload-level-value',[(dict(source='스킬2',name='level fixed',type='buff',stat='reload_time_fixed',target='all_allies',values={'1':.454,'10':.0004},trigger={'timing':['battle_start'],'condition':[]},duration=-1),NAMES[0])]),
  ('fixed-reload-lazy-not-resolved',[(E('lazy fixed','buff','reload_time_fixed',.01,'allies_top_atk:1'),NAMES[0])]),
  ('fixed-reload-conditional-marker-still-active',[(E('conditional fixed','buff','reload_time_fixed',.27,'all_allies',event='passive',condition=['during_full_burst']),NAMES[0])]),
 ]:yield label,es

def verify_primitives(device,backend):
 out=[]
 for label,effects in primitives():
  chars=oracle.characters(NAMES);program=oracle.program(chars,effects);bs={n:{'atk':100000+i*1234.567,'hp':1000000+i*345678.9,'def':1000} for i,n in enumerate(NAMES)}
  script=[[0,0,0,i,0,-1,0,0] for i in range(5)];qi=0
  for t in [0,.2,.5,.7,1.2]:
   script.extend([[t,0,7,0,0,-1,0,0],[t,0,3,1,0,-1,0,0]])
   for who in range(5):script.append([t,2,0,who,-1,qi,0,0]);qi+=1;script.append([t,2,107,who,0,qi,0,0]);qi+=1
  cpu,totals=oracle.oracle(program,script,[31784,17],bs);gpu=run(device,[program],script,[[31784,17]],[bs],module_backend=backend);errors=[]
  for qi,(x,y) in enumerate(zip(cpu,gpu['queries'][0])):
   fields=[0] if qi%2 else [0,1,36]
   for k in fields:
    if not math.isclose(x[k],y[k],rel_tol=1e-12,abs_tol=1e-8):errors.append([qi,k,x[k],y[k]])
  c={'name':label,'passed':not errors and totals==gpu['totals'][0],'errors':errors[:12],'queries':len(cpu),'backend':backend};out.append(c);print(json.dumps(c),flush=True)
 return out

def full_scenarios():
 owner=NAMES[2]
 yield 'hp-growth-and-expiry-all-recipients',{NAMES[0]:[E('conversion','buff','atk_from_hp_pct',3,'all_allies'),E('hp grows','buff','max_hp_pct',25,'all_allies',event='burst_cast',duration=2),E('caster hp','buff','hp_caster_based_pct',13,'all_allies',event='full_burst_start',duration=3)]},12
 yield 'hp-stack-and-remove-refresh',{owner:[E('conversion','buff','atk_from_hp_pct',1,event='on_attack',max_stack=5,duration=1),E('HP growth','buff','max_hp_only_pct',20,event='on_attack',max_stack=3,duration=2)]},12
 for i in [0,2,3,4]:
  yield 'force-reload-base-'+str(i),{NAMES[i]:[E('fixed time','buff','reload_time_fixed',.23),E('force','instant','force_reload',0,event='every:0.7s'),E('completion buff','buff','atk_pct',10,event='event:full_reload',max_stack=10)]},8
 yield 'force-reload-overlap-does-not-restart',{owner:[E('fixed time','buff','reload_time_fixed',.9),E('force','instant','force_reload',0,event='every:0.2s'),E('completion','buff','atk_pct',10,event='event:full_reload',max_stack=10)]},8
 yield 'zero-fixed-reload-at-battle-start',{owner:[E('zero reload','buff','reload_time_fixed',0),E('force now','instant','force_reload',0),E('completion','buff','atk_pct',10,event='event:full_reload',max_stack=10)]},8
 yield 'last-fire-can-interrupt-instant-charge',{owner:[E('single round','buff','max_ammo_flat',-1000),E('instant charge','buff','charge_speed_pct',100),E('fixed time','buff','reload_time_fixed',.1),E('force at start','instant','force_reload',0,event='last_bullet_fire')]},6
 yield 'force-at-full-charge-still-fires',{owner:[E('fixed time','buff','reload_time_fixed',.2),E('force in fire','instant','force_reload',0,event='full_charge'),E('completion','buff','atk_pct',10,event='event:full_reload',max_stack=10)]},8
 for kind in ['SMG','SR']:
  yield 'mode-fixed-reload-force-'+kind,{owner:[modes.mode(kind,max_ammo=4,duration=4,charge_time=.3),E('fixed time','buff','reload_time_fixed',.2),E('force','instant','force_reload',0,event='every:0.7s')]},12
 yield 'fixed-reload-expires-mid-reload',{owner:[E('fixed window','buff','reload_time_fixed',.73,duration=1),E('force','instant','force_reload',0,event='every:0.7s'),E('fast normal','buff','reload_speed_pct',99)]},8

@contextmanager
def observed_reloads():
 from calculator.timeline import CharState
 start=CharState._start_reload;finish=CharState._finish_reload;counts={'starts':0,'finishes':0,'fixed_times':[]}
 def start_reload(self,t,bm,*args,**kw):
  counts['starts']+=1;v=self._fixed_reload_time(bm)
  if v is not None:counts['fixed_times'].append(v)
  return start(self,t,bm,*args,**kw)
 def finish_reload(self,*args,**kw):counts['finishes']+=1;return finish(self,*args,**kw)
 CharState._start_reload=start_reload;CharState._finish_reload=finish_reload
 try:yield counts
 finally:CharState._start_reload=start;CharState._finish_reload=finish

def verify(device,backend,include_real=True):
 out=verify_primitives(device,backend)
 for label,effects,seconds in full_scenarios():
  try:
   with p.custom_effects(effects),observed_reloads() as observed:c=p.full.compare(device,label,body_for(NAMES,seconds,True),module_backend=backend)
   c['reload_observations']=observed
   if label.startswith(('force-','mode-fixed','fixed-reload','zero-fixed','last-fire')):c['passed'] &= observed['starts']>0 and bool(observed['fixed_times'])
  except (Exception,SystemExit) as e:c={'name':label,'passed':False,'error':str(e)}
  c['backend']=backend;out.append(c);print(json.dumps(c,ensure_ascii=True),flush=True)
 if include_real:
  before=json.loads((ROOT/'research/detail-coverage-modes.json').read_text(encoding='utf-8'));was={r['character'] for r in before['results'] if r['supported']}
  for r in coverage()['results']:
   if not r['supported'] or r['character'] in was:continue
   name=r['character'];names=[name]+[n for n in ['리타','크라운','앨리스','모더니아','N102'] if n!=name][:4]
   try:
    with observed_reloads() as observed:c=p.full.compare(device,'real-'+name,body_for(names,60,True),module_backend=backend)
    c['reload_observations']=observed
   except (Exception,SystemExit) as e:c={'name':name,'passed':False,'error':str(e)}
   c['backend']=backend;out.append(c);print(json.dumps(c,ensure_ascii=True),flush=True)
  # A newly accepted favorite variant and level-dependent fixed reload values.
  for name,stage,level in [('엑시아',3,10),('질',0,1),('질',0,7)]:
   names=[name]+[n for n in ['리타','크라운','앨리스','모더니아','N102'] if n!=name][:4];body=body_for(names,60,True);body['profile']['chars'][name]['favorite_stage']=stage;body['profile']['chars'][name]['skill_levels']['3']=level
   try:
    with observed_reloads() as observed:c=p.full.compare(device,f'real-{name}-favorite{stage}-burst{level}',body,module_backend=backend)
    c['reload_observations']=observed;c['passed'] &= bool(observed['fixed_times'])
   except (Exception,SystemExit) as e:c={'name':name,'passed':False,'error':str(e)}
   c['backend']=backend;out.append(c);print(json.dumps(c,ensure_ascii=True),flush=True)
 return out
if __name__=='__main__':
 d=Cuda()
 try:cases=verify(d,'native')+verify(d,'ptx')
 finally:d.close()
 files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/verify-detail.py','scripts/verify-health-reload-detail.py']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'cpu_trace_used_as_gpu_input':False,'scope':'HP-to-ATK, fixed/forced reload primitives and complete squads; static enemy expected full-charge model, not all characters/effects','cases':cases,'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}}
 (ROOT/'research/detail-health-reload-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
