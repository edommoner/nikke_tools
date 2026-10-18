"""Whole-squad weapon-mode differential checks against the pinned CPU engine."""
import sys,json,importlib.util,hashlib
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import body_for,coverage,a
from gpu_selector import Cuda
spec=importlib.util.spec_from_file_location('mode_periodic',ROOT/'scripts/verify-periodic-detail.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

def mode(weapon='SR',**kw):
 return {'source':'스킬3','name':'mode','type':'weapon_change','target':'self','weapon_type':weapon,'damage_coeff':{'10':251},'max_ammo':3,'trigger':{'timing':['burst_cast'],'condition':[]},**kw}

def scenarios():
 out=[];owner=p.NAMES[2]
 for label,eff in [
  ('finite-charge-shot-limit',mode(duration_bullets=3,charge_time=.4,full_charge_mult=275)),
  ('charge-entry-reload',mode(duration_bullets=3,charge_time=.4,entry_reload=True)),
  ('charge-expiry',mode(duration=2.13,max_ammo=-1,charge_time=.4)),
  ('finite-auto-shot-limit',mode('SMG',max_ammo=4,duration_bullets=4)),
  ('finite-auto-reload',mode('SMG',max_ammo=4,reload_time=.3)),
  ('finite-auto-expiry',mode('SMG',max_ammo=2,duration=3)),
  ('first-coeff',mode('SG',charge=True,max_ammo=3,duration_bullets=3,charge_time=.25,first_damage_coeff={'10':1800})),
  ('skill-charge',mode('RL',max_ammo=-1,duration=4,charge_time=.5,full_charge_mult=250,skill_damage=True,core_dmg_mult=300)),
  ('fixed-ammo',mode('SMG',max_ammo=4,duration_bullets=4)),
  ('buffed-ammo',mode('SMG',max_ammo=4,duration_bullets=4,max_ammo_buff_applies=True)),
  ('scaled-ammo-missing',mode('SMG',max_ammo=4,duration_bullets=4,max_ammo_scaling_ref='absent')),
  ('shot-end-removes-ammo',mode(duration_bullets=3,charge_time=.2)),
  ('scaled-ammo-zero',mode('SMG',max_ammo=4,duration_bullets=4,max_ammo_scaling_ref='zero gauge')),
  ('scaled-ammo-positive',mode('SMG',max_ammo=2,duration_bullets=2,max_ammo_scaling_ref='zero gauge')),
  ('charge-cover-auto-reload',mode(max_ammo=2,duration=4,charge_time=.2,cover_during_delay=True)),
 ]:
  effects=[eff]
  if 'ammo' in label:effects.append(p.effect('ammo bonus','buff','max_ammo_pct',50))
  if label=='shot-end-removes-ammo':effects.append(p.effect('empty on end','instant','ammo_charge_pct',-100,event='event:state_end:mode'))
  if label=='skill-charge':effects += [p.effect('normal only','buff','normal_atk_dmg_pct',70),p.effect('one bullet','buff','atk_pct',10,duration_bullets=1)]
  if label.startswith('scaled-ammo-') and label!='scaled-ammo-missing':effects.insert(0,p.effect('gauge setup','instant','gauge_charge',0 if label.endswith('zero') else 3,gauge_id='zero gauge',gauge_max=10))
  if label=='charge-cover-auto-reload':effects.append(p.effect('instant reload','buff','reload_speed_pct',100))
  out.append((label,{owner:effects},12))
 return out

@contextmanager
def observe_modes():
 from calculator.timeline import CharState
 original=CharState._tick_weapon_change;observed={'mode_calls':0,'mode_shots':0,'effects':{}}
 def tick(self,t,bm,enemy,cfg,eff):
  observed['mode_calls']+=1;name=eff.get('name','');observed['effects'][name]=observed['effects'].get(name,0)+1
  before=self._wc_shots;result=original(self,t,bm,enemy,cfg,eff);observed['mode_shots']+=max(0,self._wc_shots-before);return result
 CharState._tick_weapon_change=tick
 try:yield observed
 finally:CharState._tick_weapon_change=original

def verify(device,backend,include_real=True):
 out=[]
 for label,effects,seconds in scenarios():
  try:
   with p.custom_effects(effects),observe_modes() as observed:c=p.full.compare(device,label,body_for(p.NAMES,seconds,True),module_backend=backend)
   c['mode_observations']=observed;c['passed'] &= observed['mode_calls']>0 and (observed['mode_shots']==0 if label=='scaled-ammo-zero' else observed['mode_shots']>0)
  except (Exception,SystemExit) as e:c={'name':label,'passed':False,'error':str(e)}
  c['backend']=backend;out.append(c);print(json.dumps(c,ensure_ascii=True),flush=True)
 if include_real:
  before=json.loads((ROOT/'research/detail-coverage-probability.json').read_text(encoding='utf-8'));was={r['character'] for r in before['results'] if r['supported']}
  for r in coverage()['results']:
   if not r['supported'] or r['character'] in was:continue
   name=r['character'];names=[name]+[n for n in ['리타','크라운','앨리스','모더니아','N102'] if n!=name][:4]
   try:
    with observe_modes() as observed:c=p.full.compare(device,'real-'+name,body_for(names,60,True),module_backend=backend)
    c['mode_observations']=observed;c['passed'] &= observed['mode_shots']>0
   except (Exception,SystemExit) as e:c={'name':name,'passed':False,'error':str(e)}
   c['backend']=backend;out.append(c);print(json.dumps(c,ensure_ascii=True),flush=True)
 return out
if __name__=='__main__':
 device=Cuda()
 try:cases=verify(device,'native')+verify(device,'ptx')
 finally:device.close()
 files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','scripts/verify-modes-detail.py']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'cpu_trace_used_as_gpu_input':False,'scope':'finite/infinite auto and charge modes in whole squads, automatic bursts, owned growth; static unharmed enemy, expected mode; not all effects','cases':cases,'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}}
 (ROOT/'research/detail-modes-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
