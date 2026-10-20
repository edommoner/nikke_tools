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
 return rows
