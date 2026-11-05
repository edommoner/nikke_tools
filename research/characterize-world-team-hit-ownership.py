"""Full-native team-hit owner/attacker contract for the next shared bridge;GPU0."""
import copy,hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from world_spawn_cases import fixtures as spawn_fixtures
from world_enemy_attack_cases import field
from world_frame_native import observe,roster_names
from calculator.buff_manager import BuffManager

def fixtures():
 base=copy.deepcopy(spawn_fixtures()[0]);base['duration']=.35;base['patterns']=[dict(id='idle',kind='idle',until=dict(time=.35))];base['observe_enemy_spawn']=False;rows=[]
 for family,parts in [('part',True),('body',False)]:
  for target in ('self','all_allies'):
   c=copy.deepcopy(base);c.update(name=family+'-owner4-target-'+target,effects=[field('atk_pct',1,target,'team-witness',family+'_hit_count:1',max_stack=128)],owners=[4],state_queries=[(0,0,0,1,'team-witness')]);c['enemy']['has_parts']=parts;rows.append(c)
 c=copy.deepcopy(rows[0]);c['name']='part-owner4-condition-attacker-is-not-condition-owner';c['effects'][0]['trigger']['condition']=['self_hp_above:99'];c['patterns'].append(dict(id='damage-owner',kind='attack',delay=.05,spec=dict(atk=500,coeff=100,target='slot:5',hits=1)));rows.append(c)
 c=copy.deepcopy(rows[0]);c['name']='part-three-pellets-team-counter';c['effects'][0]['trigger']['timing']=['part_hit_count:3'];c['combat']['weapons'][0].update(base_weapon_type='SG',pellets=3,muzzles=2);rows.append(c)
 return rows
