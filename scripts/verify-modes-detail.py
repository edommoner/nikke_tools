"""Whole-squad weapon-mode differential checks against the pinned CPU engine."""
import sys,json,importlib.util,hashlib
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import body_for,coverage,a
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
