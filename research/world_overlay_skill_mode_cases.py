"""Authored physical skill-mode semantics,shared by CUDA and Metal validation."""
import copy,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def fixtures():
 s=importlib.util.spec_from_file_location('skill_mode_gates',ROOT/'research/world_overlay_gate_cases.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
 base=next(c for c in g.fixtures() if c['name']=='shield-normal-weapon-change');rows=[]
 def add(name,patterns,skill=True):
  c=copy.deepcopy(base);c['name']='weapon-mode-'+name;c['patterns']=patterns;c['effects'][0]['skill_damage']=skill;rows.append(c);return c
 idle=lambda:[dict(id='open',kind='idle')]
 vanish=lambda:[dict(id='vanish',kind='vanish',until={'time':.25})]
 shield=lambda:[dict(id='shield',kind='shield',code='수냉',until={'time':.25})]
 for skill in (False,True):
  for name,patterns in [('open',idle()),('vanish',vanish()),('shield-block',shield()),('shield-pass',shield())]:
   c=add(name+'-'+str(skill),patterns,skill)
   if name=='shield-pass':c['element_codes']=['전격']*5
 for field,value in [('normal_atk_dmg_pct',100),('normal_atk_crit_rate',100),('normal_atk_crit_dmg',100),('crit_rate',100),('atk_pct',100)]:
  c=add('buff-'+field,idle());c['effects'].append(dict(name=field,source='스킬1',type='buff',stat=field,fixed_value=value,target='self',duration=-1,trigger=dict(timing=['battle_start'],condition=[])));c['owners'].append(0)
 for core in (0,52):
  c=add('core-'+str(core),idle());c['enemy']['core_px']=core
 for distance in (15,30):
  c=add('distance-'+str(distance),idle());c['enemy']['distance']=distance;c['enemy']['optimal_range_weapons']=[]
 c=add('finite-bullet-buff-skips-consumption',idle());c['effects'].append(dict(name='one-normal-shot',source='스킬1',type='buff',stat='atk_pct',fixed_value=100,target='self',duration=-1,duration_bullets=1,trigger=dict(timing=['battle_start'],condition=[])));c['owners'].append(0)
 for kind in ('vanish','shield'):
  c=add('one-shot-exit-before-landing-'+kind,vanish() if kind=='vanish' else shield());c['effects'][0]['duration_bullets']=1
  c=add('pellets-muzzles-'+kind,vanish() if kind=='vanish' else shield());c['effects'][0].update(pellets=3,muzzles=2)
  c=add('charge-'+kind,vanish() if kind=='vanish' else shield());c['duration']=1.2;c['effects'][0].update(weapon_type='SR',charge=True,charge_time=.2,full_charge_mult=300,post_fire_delay=.2,fire_rate=5,fire_rate_max=5)
 for skill in (False,True):
  c=add('muzzles-only-vanish-'+str(skill),vanish(),skill);c['effects'][0].update(pellets=1,muzzles=2)
 c=add('normal-charge-camera-vanish',vanish(),False);c['duration']=1.2;c['effects'][0].update(weapon_type='SR',charge=True,charge_time=.2,full_charge_mult=300,post_fire_delay=.2,fire_rate=5,fire_rate_max=5)
 c=add('skill-charge-unobserved-vanish',vanish());c['duration']=1.2;c['camera']=[];c['camera_mode']='single';c['effects'][0].update(weapon_type='SR',charge=True,charge_time=.2,full_charge_mult=300,post_fire_delay=.2,fire_rate=5,fire_rate_max=5)
 c=add('vanish-unobserved-auto-still-pauses',vanish());c['camera']=[];c['camera_mode']='single'
 return rows
