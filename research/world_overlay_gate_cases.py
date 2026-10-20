"""Authored gate/cadence/gauge fixtures,shared without backend branches."""
import copy,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def fixtures():
 spec=importlib.util.spec_from_file_location('gate_bodies',ROOT/'research/verify-world-overlay-body.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
 base=copy.deepcopy(b.cases()[0]);base.update(observe_overlay=True,element_codes=['작열']*5)
 for w in base['combat']['weapons']:w['gauge']=.25
 base['weapon_metadata']['burst_energy_raw']=.125
 rows=[]
 def add(name,patterns,camera=()):
  c=copy.deepcopy(base);c.update(name=name,patterns=patterns,camera=list(camera),camera_mode='shared' if len(camera)>1 else 'single');rows.append(c);return c
 v=lambda **kw:dict(id='vanish',kind='vanish',until={'time':.25},**kw)
 sh=lambda code='수냉',**kw:dict(id='shield',kind='shield',code=code,until={'time':.25},**kw)
 add('vanish-unobserved-auto-pauses', [v()])
 add('vanish-observed-auto-blocks',[v()],[b.f.NAMES[0]])
 add('vanish-shared-camera-blocks',[v()],b.f.NAMES)
 c=add('vanish-mid-magazine-forces-reload',[v(delay=.1)])
 for w in c['combat']['weapons']:w.update(reload=.2,capacity=5)
 add('shield-normal-damage-blocks-but-gauge-gains',[sh()],b.f.NAMES)
 c=add('shield-base-element-passes',[sh()],b.f.NAMES);c['element_codes']=['전격']*5
 add('shield-two-openings-in-declaration-order',[sh(),dict(id='other',kind='shield',code='풍압',until={'time':.25})],b.f.NAMES)
 add('shield-opening-order-before-declaration',[dict(id='declared-first',kind='shield',code='풍압',delay=.1,until={'time':.25}),sh()],b.f.NAMES)
 add('vanish-before-both-shields',[sh(),v(),dict(id='other',kind='shield',code='풍압',until={'time':.25})],b.f.NAMES)
 for code in ('수냉','풍압',None):
  c=add('shield-override-'+str(code),[sh()],b.f.NAMES)
  c['effects']=[b.f.effect('element_code_override',0,target='all_allies',duration=.2,target_code=code)];c['owners']=[0]
 for kind in ('shield','vanish'):
  for normal_formula in (False,True):
   c=add(kind+'-named-skill-'+str(normal_formula),[sh() if kind=='shield' else v()],b.f.NAMES)
   c['effects']=[dict(name='named-skill',source='스킬1',type='damage',stat='auto_damage' if normal_formula else 'bonus_damage',fixed_value=100,target='all_enemies',trigger=dict(timing=['battle_start'],condition=[]))];c['owners']=[0]
 for kind in ('shield','vanish'):
  c=add(kind+'-blocked-packets-do-not-lifesteal',[sh() if kind=='shield' else v(),dict(id='incoming',kind='attack',spec=dict(atk=200,coeff=100,target='all',hits=1))],b.f.NAMES)
  c['effects']=[b.f.effect('lifesteal_pct',100,target='all_allies')];c['owners']=[0]
 c=add('shield-pellets-and-muzzles-account-each-hit',[sh()],b.f.NAMES)
 for w in c['combat']['weapons']:w.update(pellets=3,muzzles=2)
 for camera in ((),b.f.NAMES):
  c=add('vanish-charge-'+('camera' if camera else 'unobserved'),[v()],camera);c['duration']=1.2
  for w in c['combat']['weapons']:w.update(mode='charge',base_weapon_type='SR',charge=.2,interval=.2,min_cycle=.2,full_charge_mult=300,gauge_mult=300 if camera else 100)
 c=add('vanish-mg-warmup-cools-by-actual-idle',[v(delay=.55)]);c['duration']=1.5
 from calculator import timeline
 for w in c['combat']['weapons']:w.update(mode='auto_warmup',base_weapon_type='MG',rate=5,rate_max=10,warmup=5,cooldown_time=timeline._MECHANICS['weapon_type_defaults']['MG']['cooldown_time'],interval=.2,reload=.2,capacity=5)
 for kind in ('shield','vanish'):
  c=add(kind+'-normal-weapon-change',[sh() if kind=='shield' else v()],b.f.NAMES)
  c['effects']=[dict(name='ordinary-mode',source='스킬1',type='weapon_change',weapon_type='AR',damage_coeff=100,max_ammo=-1,fire_rate=10,fire_rate_max=10,charge=False,pellets=1,muzzles=1,post_fire_delay=0,burst_energy=.25,core_dmg_mult=200,target='self',duration=.3,trigger=dict(timing=['battle_start'],condition=[]))];c['owners']=[0]
 for enabled in (False,True):
  c=add('pending-b3-'+('shield-at-landing' if enabled else 'open'),[dict(id='later-shield',kind='shield',code='수냉',delay=.3,until={'time':.5})] if enabled else [dict(id='open',kind='idle')],b.f.NAMES);c['duration']=1
  for i,w in enumerate(c['combat']['weapons']):w['stage']=i+1 if i<3 else 0
  c['effects']=[dict(name='fill-gauge',source='스킬1',type='instant',stat='burst_charge_pct',fixed_value=100,target='all_allies',trigger=dict(timing=['battle_start'],condition=[])),dict(name='pending-bonus',source='버스트',type='damage',stat='bonus_damage',fixed_value=200,target='all_enemies',trigger=dict(timing=['burst_cast'],condition=[]))];c['owners']=[0,2]
 return rows
