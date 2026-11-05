"""Literal startup/summon notification programs for the common GPU executor."""
import copy
from world_enemy_attack_cases import fixtures as attack_fixtures,field

def fixtures():
 base=copy.deepcopy(attack_fixtures()[0]);base.update(observe_enemy_spawn=True,observe_periodic_skills=True,observe_target_counters=True,duration=.5);base['patterns']=[dict(id='idle',kind='idle',until=dict(time=.5))];rows=[]
 def add(name,effects,owners=None):
  c=copy.deepcopy(base);c.update(name=name,effects=effects,owners=owners if owners is not None else [0]*len(effects));c['state_queries']=[(0,0,0,1,effects[0]['name'])];rows.append(c);return c
 def buff(stat='atk_pct',value=10,target='self',name='spawn',timing='event:enemy_spawn',**kw):return field(stat,value,target,name,timing,**kw)
 add('spawn-once-idle',[buff()])
 c=add('startup-plus-two-immediate-adds',[buff(max_stack=128)]);c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=2,hp=100000)))
 c=add('startup-plus-two-delayed-adds',[buff(max_stack=128)]);c['patterns'].append(dict(id='wave',kind='summon',delay=.2,spec=dict(count=2,hp=100000)))
 c=add('startup-plus127-adds',[buff(max_stack=128)]);c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=127,hp=1000000)))
 c=add('reopened-generation-notifies-each-time',[buff(max_stack=128)]);c['patterns'].append(dict(id='wave',kind='summon',after=['start','wave'],repeat=0,until=dict(time=.1),spec=dict(count=1,hp=100000)))
 add('all-five-owners-startup',[buff(name='owner'+str(i)) for i in range(5)],owners=list(range(5)))
 add('all-battle-start-owners-before-spawn',[buff(name='late-seed',timing='battle_start',target='all_allies',value=0),buff(name='spawn',condition=['self_state:late-seed'])],owners=[4,0])
 add('spawn-before-magazine-initialization',[buff(stat='max_ammo_flat',value=50)])
 add('spawn-after-battle-start-ammo-buff',[buff(stat='max_ammo_flat',value=10,timing='battle_start',name='initial-ammo'),buff(stat='max_ammo_pct',value=50)])
 add('spawn-cooldown-gauge-resource',[dict(name='charge',source='스킬1',type='instant',stat='burst_charge_pct',fixed_value=25,target='all_allies',trigger=dict(timing=['event:enemy_spawn'],condition=[]))])
 for target in ('boss','target','all_enemies','enemies_nearest:2'):
  c=add('spawn-enemy-field-'+target,[buff(stat='received_dmg_pct',value=25,target=target,max_stack=128)]);c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=2,hp=100000)))
 for family in ('bonus_damage','dot_damage'):
  e=dict(name='spawn-damage',source='스킬1',type='damage',stat=family,fixed_value=25,target='all_enemies',trigger=dict(timing=['event:enemy_spawn'],condition=[]))
  if family=='dot_damage':e.update(duration=.35,tick_interval=.1,tick_start='immediate')
  c=add('spawn-'+family,[e]);c['patterns'].append(dict(id='wave',kind='summon',delay=.2,spec=dict(count=1,hp=100000)))
 for family in ('bonus_damage','dot_damage'):
  c=copy.deepcopy(next(c for c in rows if c['name']=='spawn-'+family));c['name']='spawn-'+family+'-all128-once';c['effects'][0]['max_trigger']=1;c['patterns']=[dict(id='wave',kind='summon',spec=dict(count=127,hp=1000000))];rows.append(c)
 for limit in (1,2):
  c=add('spawn-global-trigger-limit-'+str(limit),[buff(max_stack=128,max_trigger=limit)]);c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=3,hp=100000)))
 c=add('spawn-after-initial-vanish',[buff()]);c['patterns'].append(dict(id='gate',kind='vanish',until=dict(time=.25)))
 c=add('spawn-same-frame-delayed-attack',[buff(stat='atk_caster_based_pct',value=-10,target='boss',max_stack=128)]);c['patterns']=[dict(id='attack',kind='attack',delay=.2,spec=dict(atk=500,coeff=100,target='all',hits=1)),dict(id='wave',kind='summon',delay=.2,spec=dict(count=1,hp=100000))]
 return rows
