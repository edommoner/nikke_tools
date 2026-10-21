"""Native startup and per-add event ordering, with GPU calls forbidden."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from unittest.mock import patch
from world_spawn_cases import fixtures
from world_skill_native import inspect

def main():
 rows=[]
 with patch('portable_backend.build',side_effect=AssertionError('GPU build forbidden')),patch('portable_backend.execute',side_effect=AssertionError('GPU execution forbidden')):
  for c in fixtures():
   native,trace=inspect(c);rows.append(dict(name=c['name'],case=c,native=native,skill_trace=trace))
 r=dict(passed=False,cases=rows,full_native_battles=len(rows),gpu_builds=0,gpu_executions=0,full_goal_complete=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['research/world_spawn_cases.py','research/world_spawn_native.py','research/world_frame_native.py','research/characterize-world-spawn.py']})
 p=ROOT/'research/portable-world-spawn-native-contract.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');by={x['name']:x for x in rows}
 for name,count in [('spawn-once-idle',5),('startup-plus-two-immediate-adds',15),('startup-plus-two-delayed-adds',15),('startup-plus127-adds',640)]:
  notes=by[name]['native']['enemy_spawn_notifications'];assert len(notes)==count and [n['owner'] for n in notes]==list(range(5))*(count//5)
 accumulated=0.0
 for _ in range(12):accumulated+=1/60
 notes=by['startup-plus-two-delayed-adds']['native']['enemy_spawn_notifications'];assert all(n['time']==0 for n in notes[:5]) and all(n['time']==accumulated for n in notes[5:])
 assert by['all-battle-start-owners-before-spawn']['native']['named_state']['allied_carriers'][-1]['name']=='spawn'
 assert by['spawn-before-magazine-initialization']['native']['ammo'][0]>1000
 r.update(passed=True,startup_team_spawn_after_all_battle_start=True,one_team_notice_per_add=True,spawn_before_initial_magazine=True);p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('Native enemy spawn',len(rows),'battles;startup/add/ordering exact;GPU0')
if __name__=='__main__':main()
