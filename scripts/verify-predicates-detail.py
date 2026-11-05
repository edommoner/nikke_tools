"""Independent defense, persona, immunity and static-enemy predicate parity."""
import sys,json,math,hashlib,copy,importlib.util
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import body_for,coverage
spec=importlib.util.spec_from_file_location('predicate_lists_oracle',ROOT/'scripts/verify-lists-detail.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
E=base.E;oracle=base.oracle;periodic=base.periodic;NAMES=base.NAMES

def primitives():
 out=[]
 def queries(t):return [(t,'query',i) for i in range(5)]
 def build(name,effects,expected,commands=None,chars=None):
  p=oracle.program(chars or oracle.characters(NAMES),[(e,NAMES[i]) for i,e in effects]);script=[[0,0,0,i,0,-1,0,0] for i in range(5)];qi=0
  for t,op,who in commands or queries(.1):
   if op=='query':script.append([t,2,0,who,-1,qi,0,0]);qi+=1
   else:script.append([t,0,op,who,0,-1,0,0])
  out.append((name,p,script,expected))
 defense=lambda value,target='self',**kw:E('defense','buff','def_pct',value,target,**kw)
 select=lambda target='allies_below_def',value=7,**kw:E('selected','buff','atk_pct',value,target,**kw)
 build('below-defense-uses-live-percent-buffs',[(0,defense(100)),(3,select())],[0,7,7,0,0])
 build('below-defense-uses-caster-based-flat-defense',[(0,E('flat defense','buff','def_caster_based_pct',100,NAMES[3])),(3,select())],[7,7,7,0,7])
 build('below-defense-equality-is-excluded',[(0,defense(40)),(0,select())],[0,7,7,7,0])
 build('top-defense-retains-pinned-base-stat-ranking',[(0,defense(100)),(0,select('allies_top_def:1'))],[0,0,0,0,7])
 build('below-defense-list-is-eager-string-is-lazy',[(0,defense(100)),(0,select(['allies_below_def'])),(0,defense(300,NAMES[1])),(0,select(value=13))],[0,7,20,20,20])
 build('below-defense-raw-active-values-ignore-runtime-gate',[(0,E('gate','buff','',0)),(0,defense(100,condition=['self_state:gate'])),(0,E('remove','instant','remove_named_buff',0,event='burst_cast',target_effect='gate')),(3,select(['allies_below_def'],event='on_attack'))],[0,7,7,0,0],[(.1,3,0),(.2,7,3)]+queries(.3))
 marker=lambda target='self',**kw:E('persona','buff','persona_state',1,target,**kw)
 persona=lambda **kw:select('allies_burst3_persona_excl_self',**kw)
 build('persona-filters-innate-stage-and-recipient-membership',[(0,marker(NAMES[1])),(0,marker(NAMES[2])),(0,marker(NAMES[3])),(0,persona())],[0,0,7,7,0])
 build('persona-excludes-caster',[(0,marker(NAMES[2])),(0,marker(NAMES[3])),(2,persona())],[0,0,0,7,0])
 chars=oracle.characters(NAMES);chars[1]['burst_stage']='3'
 build('persona-honors-pinned-innate-stage',[(0,marker(NAMES[1])),(0,persona())],[0,7,0,0,0],chars=chars)
 build('zero-stack-persona-marker-still-counts',[(0,marker(NAMES[2],polarity='harmful')),(0,E('zero','instant','debuff_stack_remove',1,NAMES[2],event='burst_cast',target_effect='persona')),(0,persona(event='on_attack'))],[0,0,7,0,0],[(.1,3,0),(.2,7,0)]+queries(.3))
 build('persona-filter-does-not-force-lazy-marker-targets',[(3,E('strong','buff','atk_pct',100)),(0,marker('allies_top_atk:1')),(0,persona())],[0,0,0,100,0])
 build('enemy-stun-gates-at-activation-and-remains-latched',[(0,E('stun','buff','stun',1,'target',duration=.1)),(0,select('self',condition=['target_stunned']))],[7,0,0,0,0],queries(.2))
 build('same-frame-expired-stun-still-gates-activation',[(0,E('stun','buff','stun',1,'target',duration=0)),(0,select('self',condition=['target_stunned']))],[7,0,0,0,0])
 build('enemy-stun-immunity-suppresses-until-removed',[(0,E('immune','buff','stun_immune',1,'target')),(0,E('stun','buff','stun',1,'target')),(0,E('remove','instant','remove_named_buff',0,event='on_attack',target_effect='immune')),(0,select('self',event='on_attack',condition=['target_stunned']))],[0,0,0,0,0]+[7,0,0,0,0],queries(.1)+[(.2,7,0)]+queries(.3))
 build('allied-stun-immunity-expiry-restores-existing-stun',[(0,E('stun','buff','stun',1,NAMES[3])),(3,E('immune','buff','stun_immune',1,duration=.1)),(3,select('self',condition=['self_stun_immune']))],[0,0,0,7,0]*2,queries(.05)+queries(.2))
 from calculator.buff_manager import char_effects
 mode=copy.deepcopy(next(e for e in char_effects(NAMES[3]) if e['type']=='weapon_change'));mode['trigger']={'timing':['burst_cast'],'condition':[]};mode['duration']=.5
 for state,expected in [('무기 변경',[0,7,0]),('',[7,0,7])]:
  build('persistent-self-state-'+('generic-mode' if state else 'empty-mode'),[(3,mode),(3,select('self',event='passive',condition=['self_state:'+state]))],expected,[(.01,'query',3),(.1,3,3),(.2,'query',3),(.7,'query',3)])
 return out

def full_scenarios():
 n=NAMES
 for code in (None,'풍압','전격'):
  effects={n[0]:[E('wind','buff','atk_pct',25,'all_allies',event='passive',condition=['target_code:풍압'])],n[1]:[E('electric','buff','crit_dmg',15,'all_allies',event='passive',duration=1,condition=['target_code:전격'])]}
  yield 'full-enemy-code-'+str(code),effects,8,{'code':code}
 yield 'full-enemy-count-and-boss-add-gates',{n[0]:[E('single','buff','atk_pct',20,'all_allies',event='passive',condition=['enemy_count_below:1']),E('multiple','buff','atk_pct',100,'all_allies',event='passive',condition=['enemy_count_above:2'])],n[1]:[E('boss','buff','crit_dmg',15,'all_allies',event='burst_cast',condition=['target_is_boss']),E('add','buff','crit_dmg',100,'all_allies',event='burst_cast',condition=['target_is_add'])]},10,{}
 yield 'full-live-defense-targets-and-lists',{n[0]:[E('def shift','buff','def_pct',100,n[3],event='every:2s',duration=1),E('flat','buff','def_caster_based_pct',50,n[3],event='burst_cast',duration=5)],n[3]:[E('lower','buff','atk_pct',30,'allies_below_def',event='every:1s',duration=3,max_stack=3),E('eager lower','buff','crit_dmg',15,['self','allies_below_def'],event='burst_cast',duration=5)]},12,{}
 yield 'full-persona-recipient-snapshots',{n[2]:[E('persona','buff','persona_state',1,event='every:2s',duration=1)],n[3]:[E('other persona','buff','persona_state',1,event='burst_cast',duration=4)],n[0]:[E('persona bonus','buff','atk_pct',20,'allies_burst3_persona_excl_self',event='every:0.5s',duration=2,max_stack=3)]},12,{}
 yield 'full-enemy-stun-and-allied-immunity',{n[0]:[E('stun','buff','stun',1,'target',event='every:2s',duration=1),E('stun bonus','buff','atk_pct',20,'all_allies',event='on_attack',duration=.5,condition=['target_stunned'])],n[3]:[E('self stun','buff','stun',1,event='every:1s',duration=.3),E('immune','buff','stun_immune',1,event='every:2s',duration=1)]},12,{}
