"""Save actual native attack-field consumption before enabling GPU admission."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from unittest.mock import patch
from portable_backend import build,execute
from world_frame_native import observe
from world_enemy_attack_cases import fixtures

def main():
 rows=[]
 with patch('portable_backend.build',side_effect=AssertionError('GPU build forbidden')),patch('portable_backend.execute',side_effect=AssertionError('GPU execution forbidden')):
  for c in fixtures():
   rows.append(dict(name=c['name'],case=c,native=observe(c)))
 report=dict(passed=False,cases=rows,full_native_battles=len(rows),gpu_builds=0,gpu_executions=0,enemy_attack_gpu_connected=False,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['research/world_enemy_attack_cases.py','research/world_frame_native.py','research/characterize-world-enemy-attack.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']},full_goal_complete=False,full_character_verified=0,normal_ui='CPU',canonical_world_admission=False)
 p=ROOT/'research/portable-world-enemy-attack-native-contract.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 by={r['name']:r['native'] for r in rows};hits=lambda name:[x['damage'] for x in by[name]['hits']]
 baseline=hits('enemy-attack-baseline');assert len(baseline)==20
 for target in ('boss','target','all_enemies'):
  assert hits('atk_pct-'+target)==baseline
  assert hits('atk_caster_based_pct-'+target)==hits('atk_caster_based_pct-boss')
 assert hits('atk_caster_based_pct-boss')==[x-100 for x in baseline]
 assert hits('caster-flat-positive')==[x+100 for x in baseline]
 assert set(hits('caster-flat-clamped-below-zero'))=={1.0}
 assert hits('caster-flat-uses-base-not-buffed-caster')==hits('atk_caster_based_pct-boss')
 assert hits('caster-flat-expiry')[:10]==hits('atk_caster_based_pct-boss')[:10] and hits('caster-flat-expiry')[10:]==baseline[10:]
 report.update(passed=True,atk_pct_does_not_change_native_incoming_damage=True,caster_flat_reads_base_attack=True,caster_flat_applied_before_defense_and_clamped_zero=True,finite_expiry_exact=True)
 p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Native enemy attack',len(rows),'full battles, GPU0')
if __name__=='__main__':main()
