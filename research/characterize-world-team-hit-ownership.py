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

def main():
 results=[];original=BuffManager.notify_team_hit
 with patch('portable_backend.build',side_effect=AssertionError('GPU build forbidden')),patch('portable_backend.execute',side_effect=AssertionError('GPU execute forbidden')):
  for case in fixtures():
   names=roster_names(case);notes=[]
   def notified(manager,event,t,attacker):notes.append(dict(event=event,time=t,attacker=names.index(attacker)));return original(manager,event,t,attacker)
   with patch.object(BuffManager,'notify_team_hit',notified):native=observe(case)
   results.append(dict(name=case['name'],case=case,notifications=notes,native=native))
 r=dict(passed=False,cases=results,full_native_battles=len(results),gpu_calls=0,typed_part_body_gpu_connected=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['research/characterize-world-team-hit-ownership.py','research/world_frame_native.py']})
 p=ROOT/'research/portable-world-team-hit-native-contract.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 for case in results[:4]:
  carriers=case['native']['named_state']['allied_carriers'];assert {x['owner'] for x in carriers}==set(range(5))
  for carrier in carriers:assert carrier['recipients']==([carrier['owner']] if case['case']['effects'][0]['target']=='self' else list(range(5)))
 conditional=results[4]['native']['named_state']['allied_carriers'];assert len(conditional)==5 and all(c['stack']==1 for c in conditional)
 multiple=results[5];assert sum(c['stack'] for c in multiple['native']['named_state']['allied_carriers'])==len(multiple['notifications'])//3
 r.update(passed=True,team_condition_owner_and_activation_attacker_are_distinct=True,global_counter_shared_across_attackers=True);p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('Team part/body native',len(results),'battles;condition owner and activation attacker distinct;GPU0')
if __name__=='__main__':main()
