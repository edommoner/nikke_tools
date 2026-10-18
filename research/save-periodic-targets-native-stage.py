"""Freeze timer target/ownership semantics before ordered instant indexing."""
from checkpoint_receipts import checked_receipts,save_checkpoint
reports=['research/periodic-targets-'+n+'.json' for n in ('native','mutations-native-stage','unit-stage','before','normal-before')]
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==5 and all(c['workspace_bytes']==1259104 for c in r[reports[0]]['cases'])
assert r[reports[0]]['controls']['rejected']==2 and r[reports[1]]['cases'][0]['observations']==22 and r[reports[2]]['tests_run']==107
assert r[reports[4]]['total_damage']==692308676 and r[reports[4]]['positive_frames']==301
files=reports+['research/save-periodic-targets-native-stage.py','research/checkpoint_receipts.py','research/benchmark-periodic-targets.py','research/verify-enemy-fields-normal-witness.py','research/enemy-fields-api-fixture.json','app/periodic_target_runtime.py','app/periodic_target_specs.py','app/world_actor_runtime.py','app/impact_runtime.py','app/effect_spec.py','app/enemy_recipient_specs.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/periodic_target_cases.py','scripts/verify-periodic-targets-detail.py','scripts/verify-common-runtime-unit.py','tests/test_periodic_target_runtime.py','tests/test_enemy_recipient_runtime.py']
print(save_checkpoint('research/periodic-targets-native-stage.json','research/ports/v80-periodic-targets-native-stage',dict(passed=True,objective_complete=False,abi='detail_periodic_targets_v80',workspace_bytes=1259104,portable_verified=False,normal_summon_admission=False,normal_automatic_aim=False),files))
