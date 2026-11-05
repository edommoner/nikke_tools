"""Authored victim policies; no native selection/state is used to build GPU input."""
import copy,itertools,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def marker(name,stat,owner,target='self',value=0,duration=-1,conditions=None,timing='battle_start'):
 return dict(name=name,source='스킬1',type='buff',stat=stat,fixed_value=value,target=target,duration=duration,trigger=dict(timing=[timing],condition=conditions or [])),owner

def make(name,effects,rules,seed=0,allies=None,weapon=None):
 case=dict(name=name,effects=[e for e,_ in effects],owners=[o for _,o in effects],base_atk=[1000+100*i for i in range(5)],combat=dict(weapons=[dict(enabled=False,capacity=1000,stage=0,gauge=0) for _ in range(5)],targets=[dict(hp=1e12,defense=0)]),environment=dict(allies=allies or [dict(base_hp=1000000,base_defense=0,base_cover_hp=1000) for _ in range(5)]),script=[[0,4,0,0,0,-1,0,0]],expected_queries=[],enemy_targeting=dict(seed=seed,attacks={}))
 if weapon:
  owner,w=weapon;case['combat']['weapons'][owner].update(w)
 for i,rule in enumerate(rules):
  t=i/10
  if i:case['script'].append([t,4,0,0,0,-1,0,0])
  index=len(case['script']);case['enemy_targeting']['attacks'][str(index)]=rule
  case['script'].append([t,32,1,0,0,-1,1000,100])
  case['script'].append([t,2,0,0,0,i,0,0]);case['expected_queries'].append({})
 return case
