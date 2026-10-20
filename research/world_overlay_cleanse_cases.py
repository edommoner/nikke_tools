"""Authored world cleanse/count/lifecycle fixtures;no CPU state inputs."""
import copy,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def fixtures():
 s=importlib.util.spec_from_file_location('cleanse_bodies',ROOT/'research/verify-world-overlay-body.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
 base=copy.deepcopy(b.cases()[0]);base.update(observe_overlay=True,observe_cleanse=True,camera=list(b.f.NAMES),camera_mode='shared')
 base['patterns']=[dict(id='a',kind='buff',enemy=dict(def_mult=2,received_dmg_pct=-25),until={'time':.15}),dict(id='fixed',kind='buff',irremovable=True,enemy=dict(def_add=50,received_dmg_pct=-10)),dict(id='late',kind='buff',delay=.05,until={'time':.3},enemy=dict(def_mult=3,received_dmg_pct=50))]
 def effect(value=1,target='all_enemies',timing='battle_start',**extra):
  return dict(name='dispel',source='스킬1',type='instant',stat='enemy_buff_cleanse',fixed_value=value,target=target,trigger=dict(timing=[timing],condition=[]),**extra)
 rows=[]
 def add(name,effects,owners=None):
  c=copy.deepcopy(base);c.update(name=name,effects=effects,owners=owners or [0]*len(effects));rows.append(c);return c
 for value in (-1e308,-1,-.5,-5e-324,-0.0,0,.5,5e-324,.9999999999999999,1,1.9,2,31.999999999999996,32,1e308):add('cleanse-count-'+repr(value),[effect(value)])
 e=effect();e.pop('fixed_value');add('cleanse-default-missing-count',[e])
 add('cleanse-latest-open-first',[effect(1,timing='hit_count:2')])
 c=add('cleanse-declaration-tie-reverse',[effect(1)]);c['patterns'][2].pop('delay')
 c=add('cleanse-two-synchronous-operations',[effect(1),dict(effect(1),name='second-dispel')]);c['patterns'][2].pop('delay')
 c=add('cleanse-before-child-skill-keeps-current-frame',[effect(1,timing='hit_count:2'),dict(name='after-dispel-damage',source='스킬1',type='damage',stat='damage',fixed_value=100,target='all_enemies',trigger=dict(timing=['hit_count:2'],condition=[]))])
 c=add('cleanse-repeat-generation-reset',[effect(1,timing='on_attack')]);c['patterns']=[dict(id='repeat',kind='buff',after=['start','repeat'],repeat=0,until={'time':.1},enemy=dict(def_mult=2,received_dmg_pct=-25))]
 c=add('cleanse-duration-zero-remains-sampled',[effect(1)]);c['duration']=0
 for target in ('self','all_allies',['self']*21):add('cleanse-ally-target-no-body-'+str(target),[effect(2,target=target)])
 for target in ('boss','enemy','target','enemies_top_atk:1'):add('cleanse-enemy-selector-'+target,[effect(2,target=target)])
 e=effect(32);e['stat']='debuff_cleanse';add('ordinary-enemy-debuff-cleanse-does-not-dispel-world-buffs',[e])
 for value in (31.999999999999996,32):
  c=add('cleanse32-nodes-'+repr(value),[effect(value)]);c['duration']=.2;c['patterns']=[dict(id='node'+str(i),kind='buff',enemy=dict(def_add=1)) for i in range(32)]
 c=add('cleanse-all-irremovable-no-change',[effect(1e308)])
 for p in c['patterns']:p['irremovable']=True
 return rows
