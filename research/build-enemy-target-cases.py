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

def main():
 cases=[]
 for owner in range(5):
  for target in ('self','all_allies','boss'):
   taunter=0 if target=='all_allies' else owner
   for rule in ('all','slot:2','top_atk:1','random:1'):
    for ignore in ((False,) if rule=='all' else (False,True)):
     for stealth in ('none','taunter','others','all'):
      hidden=[] if stealth=='none' else [taunter] if stealth=='taunter' else [i for i in range(5) if i!=taunter] if stealth=='others' else list(range(5))
      effects=[marker('taunt','taunt',owner,target)]+[marker(f'hidden-{i}','stealth',i) for i in hidden]
      cases.append(make(f'enemy-victims-{owner}-{target}-{rule}-{ignore}-{stealth}',effects,[dict(target=rule,ignore_taunt=ignore)]))
 # Selected taunter first,then native squad projection of sampled/ranked membership.
 for order in itertools.permutations(range(3)):
  effects=[marker(f'taunt-{i}','taunt',i+2) for i in order]
  cases.append(make('enemy-multiple-taunters-'+''.join(map(str,order)),effects,[dict(target=r) for r in ('random:1','random:2','random:4','top_atk:4','slot:1,2,4,5')]))
 for seed in (0,1,19,2**32,2**64-1):
  cases.append(make('enemy-random-sequence-'+str(seed),[marker('anchor','',0)],[dict(target=r,ignore_taunt=False) for r in ['random:1','random:2','random:5','random:99','slot:5,1,3,1','random:1','top_atk:2','random:3']]*2,seed))
 # Marker magnitude never affects numeric damage,including enemy-target nonzero taunts.
 for value in (-100,0,100):
  for target in ('self','all_allies','boss'):
   cases.append(make(f'enemy-marker-magnitude-{target}-{value}',[marker('taunt','taunt',3,target,value)],[dict(target='all'),dict(target='random:2')]))
 # Runtime condition is checked for allied infinite taunts,but not the enemy branch.
 for owner in range(5):
  for target in ('self','boss'):
   effects=[marker('taunt','taunt',owner,target,conditions=['not_self_state:off']),marker('off','',owner,timing='on_attack')]
   case=make(f'enemy-runtime-condition-{owner}-{target}',effects,[dict(target='random:1')]*2)
   case['script'].insert(3,[.05,0,7,owner,0,-1,0,0]);case['enemy_targeting']['attacks']={str(int(k)+(int(k)>=3)):v for k,v in case['enemy_targeting']['attacks'].items()};cases.append(case)
 for owner in range(5):
  for pierce in (False,True):
   allies=[dict(base_hp=1000,base_defense=0,base_cover_hp=1000) for _ in range(5)]
   c=make(f'enemy-shield-death-{owner}-{pierce}',[marker('taunt','taunt',owner),marker('shield','shield_from_max_hp_pct',owner,value=10)],[dict(target='random:1')]*4,allies=allies)
   for cmd in c['script']:
    if cmd[1]==32:cmd[2]=int(pierce)
   cases.append(c)
  c=make(f'enemy-automatic-reload-cover-{owner}',[marker('anchor','',owner)],[dict(target=f'slot:{owner+1}')]*4,weapon=(owner,dict(enabled=True,mode='auto',coefficient=100,capacity=1,interval=.2,reload=1)))
  for cmd in c['script']:
   if cmd[1]==32:cmd[2]=0
  cases.append(c)
 for rule in ('all','random:2','top_atk:3'):
  c=make('enemy-split-order-'+rule,[marker('taunt','taunt',4),marker('split','received_dmg_split_even',0,'all_allies')],[dict(target=rule)]*3)
  for cmd in c['script']:
   if cmd[1]==32:cmd[2]=0
  cases.append(c)
 for owner in range(5):
  for stat in ('taunt','stealth'):
   for duration in (.1,.15):
    c=make(f'enemy-expiry-{owner}-{stat}-{duration}',[marker('marker',stat,owner,duration=duration)],[dict(target='random:2')]*4);cases.append(c)
   c=make(f'enemy-lazy-{owner}-{stat}',[marker('lazy',stat,owner,'allies_top_atk_excl:1')],[dict(target=r) for r in ('random:1','top_atk:2','random:3')]);cases.append(c)
  c=make(f'enemy-ordered-taunt-{owner}',[marker('taunt','taunt',owner,['allies_right:1','self'])],[dict(target='slot:1,2,3'),dict(target='random:3')]);cases.append(c)
  c=make(f'enemy-drop-taunt-target-{owner}',[marker('taunt','taunt',owner,'boss')],[dict(target='random:1')]*3)
  c['script'].insert(3,[.05,22,0,0,0,-1,0,0]);c['enemy_targeting']['attacks']={str(int(k)+(int(k)>=3)):v for k,v in c['enemy_targeting']['attacks'].items()};cases.append(c)
  # After a direct hit,the next top-attack victim must use the changed GPU buff state.
  c=make(f'enemy-received-hit-rank-{owner}',[marker('rank-rise','atk_pct',owner,value=100,timing='received_hit')],[dict(target=f'slot:{owner+1}'),dict(target='top_atk:1'),dict(target='random:2')]);cases.append(c)
  c=make(f'enemy-cover-disabled-{owner}',[marker('uncovered','cover_disabled',owner)],[dict(target=f'slot:{owner+1}')]*4,weapon=(owner,dict(enabled=True,mode='auto',coefficient=100,capacity=1,interval=.2,reload=1)))
  for cmd in c['script']:
   if cmd[1]==32:cmd[2]=0
  cases.append(c)
 for stat in ('taunt','stealth'):
  for owner in range(5):
   c=make(f'enemy-remove-marker-{owner}-{stat}',[marker('State',stat,owner), (dict(name='remove',source='스킬2',type='instant',stat='remove_named_buff',fixed_value=0,target='self',duration=-1,target_effect='State',trigger=dict(timing=['on_attack'],condition=[])),owner)],[dict(target='random:1')]*3)
   c['script'].insert(3,[.05,0,7,owner,0,-1,0,0]);c['enemy_targeting']['attacks']={str(int(k)+(int(k)>=3)):v for k,v in c['enemy_targeting']['attacks'].items()};cases.append(c)
 # Selection order must drive later defense changes within the same multi-victim attack.
 c=make('enemy-taunter-first-defense-callback',[marker('taunt','taunt',4),marker('guard','def_pct',4,'all_allies',50,timing='received_hit')],[dict(target='top_atk:5')],allies=[dict(base_hp=1000000,base_defense=1000,base_cover_hp=1000) for _ in range(5)])
 for cmd in c['script']:
  if cmd[1]==32:cmd[6]=3000;cmd[2]=0
 cases.append(c)
 # Even a full taunt seat must query/freeze remaining members' lazy stealth.
 c=make('enemy-full-taunt-still-resolves-stealth',[marker('State','taunt',0),marker('hidden','stealth',1,'allies_top_atk_excl:1'),(dict(name='remove',source='스킬2',type='instant',stat='remove_named_buff',fixed_value=0,target='self',duration=-1,target_effect='State',trigger=dict(timing=['on_attack'],condition=[])),0)],[dict(target='random:1')]*3)
 c['script'].insert(3,[.05,0,7,0,0,-1,0,0]);c['enemy_targeting']['attacks']={str(int(k)+(int(k)>=3)):v for k,v in c['enemy_targeting']['attacks'].items()};cases.append(c)
 for owner in range(5):
  for value in (-100,100):
   cases.append(make(f'enemy-taunt-not-outgoing-damage-{owner}-{value}',[marker('taunt','taunt',owner,'boss',value)],[dict(target='random:1')]*3,weapon=(owner,dict(enabled=True,mode='auto',coefficient=100,capacity=100,interval=.1,reload=1))))
 # Decimal text is the exact integer wire encoding across JSON/JavaScript.
 for seed in (0,1,19,2**32,2**64-1):
  c=copy.deepcopy(next(c for c in cases if c['name']=='enemy-random-sequence-'+str(seed)));c['name']='enemy-decimal-seed-'+str(seed);c['enemy_targeting']['seed']=str(seed);cases.append(c)
 #63 attacks consume627 MT words for these authored seeds,crossing the624-word boundary.
 for seed in (190,765):
  c=make('enemy-long-rng-'+str(seed),[marker('anchor','',0)],[],seed)
  for i in range(63):
   index=len(c['script']);c['enemy_targeting']['attacks'][str(index)]=dict(target='random:5');c['script'].append([0,32,1,0,0,-1,1000,100])
  cases.append(c)
 # Victim selection can occur between weapon frames;source references use the attack time.
 source=dict(name='refresh bird',source='스킬1',type='instant',stat='periodic_source_refresh',target='self',trigger=dict(timing=['battle_start'],condition=[]),periodic_source=dict(name='bird',slots=[.05,.1,-1],base_interval=1,population_reduction_pct=0))
 attack,owner=marker('source-atk','atk_pct',0,value=20);attack.update(scaling='stack_count',scaling_ref='bird')
 c=make('enemy-source-time-between-frames',[(source,0),(attack,0)],[])
 c['base_atk']=[1000,1400,1100,1000,1000];c['script'] += [[0,32,1,0,0,-1,1000,100],[0,2,0,0,0,0,0,0],[.125,32,1,0,0,-1,1000,100],[.125,2,0,0,0,1,0,0]];c['expected_queries']=[{},{}];c['enemy_targeting']['attacks']={'1':dict(target='top_atk:1'),'3':dict(target='top_atk:1')};cases.append(c)
 for c in cases:c['enemy_target_reference']=True
 (R/'tests/fixtures/portable-enemy-targets.json').write_text(json.dumps(dict(cases=cases),ensure_ascii=False,indent=2)+'\n');print(len(cases),'authored enemy victim inputs')
if __name__=='__main__':main()
