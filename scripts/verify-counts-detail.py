"""Dynamic trigger thresholds against independent CPU counters and full squads."""
import copy, hashlib, importlib.util, json, math, sys
from contextlib import contextmanager
from unittest.mock import patch
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a, body_for, coverage
spec=importlib.util.spec_from_file_location('count_control',ROOT/'scripts/verify-control-detail.py')
control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)
spec=importlib.util.spec_from_file_location('count_oracle',ROOT/'scripts/verify-detail.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
E=control.E;NAMES=control.NAMES

@contextmanager
def reductions():
 from calculator.buff_manager import BuffManager
 original=BuffManager._apply_trigger_count_reduce;observed=[]
 def apply(self,n,eff,caster,t):
  result=original(self,n,eff,caster,t)
  if result!=n:observed.append([caster,eff.get('name'),n,result,t])
  return result
 with patch.object(BuffManager,'_apply_trigger_count_reduce',apply):yield observed

def primitives():
 cases=[]
 def reducer(amount=2,target='counter result',**kw):
  return E('reduce '+str(amount),'buff','trigger_count_reduce',amount,target_effect=target,**kw)
 def listener(timing='on_attack_count:5',**kw):
  return E('counter result','buff','atk_pct',1,event=timing,max_stack=1000,**kw)
 def add(name,effects,expected,code=7,events=None):
  if events is None:events=[[(i+1)/10,0,code,0,0,-1,0,0] for i in range(9)]
  p=oracle.program(oracle.characters(NAMES),[(e,NAMES[who]) for who,e in effects])
  script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+events
  t=max(r[0] for r in script)+.01
  script.append([t,2,0,0,p['states']['counter result'],0,0,0])
  cases.append((name,p,script,expected))
 for timing,code in [('on_attack_count',7),('hit_count',8),('full_charge_fire_count',11),('full_charge_count',11),('full_charge_hit_count',12),('non_full_charge_fire_count',40),('core_hit_count',23),('core_hit',23),('crit_hit_count',22),('pellet_hit_count',20),('pellet_hit',20)]:
  add('reduced-'+timing,[(0,reducer()),(0,listener(timing+':5'))],3,code)
 add('no-reducer-keeps-original',[(0,listener())],1)
 add('same-raw-timing-group',[(0,reducer(target='representative')),(0,E('representative','buff','crit_dmg',1,event='on_attack_count:5',max_stack=100)),(0,listener())],3)
 add('raw-timing-spelling-is-distinct',[(0,reducer(target='representative')),(0,E('representative','buff','crit_dmg',1,event='on_attack_count:5')),(0,listener('on_attack_count:05'))],1)
 add('different-event-does-not-share',[(0,reducer(target='representative')),(0,E('representative','buff','crit_dmg',1,event='hit_count:5')),(0,listener())],1)
 add('sum-fractions-before-truncation',[(0,reducer(2.9)),(0,reducer(.2)),(0,listener())],4)
 add('negative-reduction-increases-threshold',[(0,reducer(-2.9)),(0,listener())],1)
 add('negative-original-threshold-is-not-preclamped',[(0,reducer(-10)),(0,listener('on_attack_count:-5'))],1)
 add('zero-threshold-clamped-at-runtime',[(0,listener('on_attack_count:0'))],9)
 add('large-reduction-clamps-to-one',[(0,reducer(100)),(0,listener())],9)
 add('expiry-restores-original-modulus',[(0,reducer(duration=.5)),(0,listener())],2)
 add('other-caster-does-not-reduce',[(1,reducer()),(0,listener())],1)
 add('empty-target-name-ignored',[(0,reducer(target='')),(0,listener())],1)
 add('runtime-condition-and-recipients-not-filtered',[(0,reducer(event='passive',condition=['during_full_burst'],target='counter result')|{'target':NAMES[1]}),(0,listener())],3)
 add('reducer-stacks-do-not-multiply-fixed-value',[(0,reducer(event='on_attack',max_stack=100)),(0,listener())],3)
 add('zero-stack-reducer-instance-still-counts',[(0,reducer(event='on_attack',max_stack=0)),(0,listener())],3)
 add('merged-reducer-retains-first-fixed-value',[(0,reducer()),(0,reducer(100)|{'name':'reduce 2'}),(0,listener())],3)
 add('zero-duration-reducer-is-inactive',[(0,reducer(duration=0)),(0,listener())],1)
 add('cumulative-burst-count-not-reduced',[(0,reducer()),(0,listener('burst_cast_count:5'))],5,3)
 add('level-placeholder-group-uses-raw-identity',[(0,reducer(target='representative')),(0,E('representative','buff','crit_dmg',1,event='hit_count:{0}',trigger_values={'10':5})),(0,listener('hit_count:{0}',trigger_values={'10':5}))],3,8)
 return cases

def full_cases():
 owner=NAMES[2]
 def r(amount=2,**kw):return E('count reducer','buff','trigger_count_reduce',amount,target_effect='extra hit',**kw)
 hit=E('extra hit','damage','damage',100,'target',event='full_charge_fire_count:5')
 yield 'charge-counter-reduction-expiry',{owner:[r(duration=9),hit]}, {},25
 yield 'partial-charge-count-reduced',{owner:[r(),{**hit,'trigger':{'timing':['non_full_charge_fire_count:5'],'condition':[]}}]}, {owner:{'tap_fire':{'rate':3.6,'release':.03}}},12
 yield 'counter-reduction-during-weapon-change',{owner:[r(event='burst_cast',duration=10),hit,{'source':'스킬3','name':'changed charge weapon','type':'weapon_change','target':'self','weapon_type':'SR','max_ammo':8,'damage_coeff':{'10':251},'charge_time':.3,'duration_bullets':8,'trigger':{'timing':['burst_cast'],'condition':[]}}]}, {},30
 yield 'same-timing-sharing-in-squad',{NAMES[0]:[E('reduce shared','buff','trigger_count_reduce',3,event='burst_cast',target_effect='representative',duration=10),E('representative','buff','atk_pct',2,event='on_attack_count:20',max_stack=100),E('other shared hit','damage','damage',100,'target',event='on_attack_count:20')]}, {},30
