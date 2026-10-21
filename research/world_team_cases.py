"""Authored team counters; all quantities and hit times remain GPU outputs."""
import copy,importlib.util
from pathlib import Path
from world_enemy_attack_cases import field
p=Path(__file__).with_name('characterize-world-team-hit-ownership.py');s=importlib.util.spec_from_file_location('team_contract_cases',p);contract=importlib.util.module_from_spec(s);s.loader.exec_module(contract)
def fixtures():
 rows=contract.fixtures()
 base=copy.deepcopy(rows[0])
 def add(name):
  c=copy.deepcopy(base);c['name']=name;rows.append(c);return c
 for n in (1,3,7):
  c=add('team-shared-budget-'+str(n));c['effects'][0]['max_trigger']=n
 for prob in (25,50,100):
  c=add('team-shared-probability-'+str(prob));c['effects'][0]['trigger']['condition']=['prob:'+str(prob)]
 c=add('part-and-body-independent-listeners');c['effects'].append(field('crit_dmg',10,'self','body-witness','body_hit_count:1'));c['owners'].append(1)
 c=add('team-two-sources-independent-budgets');c['effects'].append(field('crit_dmg',10,'self','second','part_hit_count:2',max_stack=128,max_trigger=2));c['owners'].append(3);c['effects'][0]['max_trigger']=1
 for core in (10,100):
  c=add('team-core-fraction-'+str(core));c['enemy']['core_px']=core;c['duration']=1.2
 c=add('team-source-down-counts-continue');c['patterns'].append(dict(id='kill-owner',kind='attack',delay=.05,spec=dict(atk=10000000,coeff=100,target='slot:5',hits=1)))
 c=add('team-attacker-caster-based-allies');c['effects'][0].update(stat='atk_caster_based_pct',fixed_value=10,target='all_allies');c['base_atk']=[1000,2000,3000,4000,5000]
 c=add('team-instant-heal-attacker');c['effects'][0].update(type='instant',stat='heal_hp_pct',fixed_value=10);c['patterns'].append(dict(id='damage-all',kind='attack',delay=.05,spec=dict(atk=500,coeff=100,target='all',hits=1)))
 c=add('team-instant-shared-gauge');c['effects'][0].update(type='instant',stat='burst_charge_pct',fixed_value=1,target='all_allies')
 c=add('team-child-damage-all-enemies');c['effects'][0].update(type='damage',stat='bonus_damage',fixed_value=10,target='all_enemies');c['patterns'].append(dict(id='wave',kind='summon',spec=dict(count=1,hp=10000000)))
 for mode in ('normal','skill'):
  c=add('team-charge-'+mode);c['duration']=1.2
  for w in c['combat']['weapons']:w.update(mode='charge',base_weapon_type='SR',charge=.2,interval=.4,min_cycle=.4,full_charge_mult=300,gauge_mult=100)
  if mode=='skill':
   c['effects'].insert(0,dict(name='mode',source='스킬1',type='weapon_change',weapon_type='SR',damage_coeff=100,max_ammo=-1,fire_rate=5,fire_rate_max=5,charge=True,charge_time=.2,full_charge_mult=300,pellets=3,muzzles=1,post_fire_delay=0,burst_energy=0,core_dmg_mult=200,skill_damage=True,target='self',duration=2,trigger=dict(timing=['battle_start'],condition=[])));c['owners'].insert(0,0)
 c=add('team-body-rejects-parts-listener');c['enemy']['has_parts']=False
 c=add('team-no-recipient-keeps-budget');c['effects'][0].update(target='all_allies_burst_casted',max_trigger=1)
 for c in rows:
  c['observe_fractional_hits']=True;c['observe_enemy_spawn']=True
  c['post_fire_delays']=[.215 if w.get('mode')=='charge' else 0 for w in c['combat']['weapons']]
 return rows
