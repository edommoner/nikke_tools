"""Freeze the functional GPU receiver executor before reducing preparation."""
from checkpoint_receipts import checked_receipts,save_checkpoint
reports=['research/enemy-fanout-native.json','research/fanout-fields-native-stage.json','research/enemy-fanout-unit-native-stage.json','research/gpu-fanout-before.json','research/fanout-normal-before.json','research/fanout-before-api.json']
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==4 and all(c['workspace_bytes']==1274400 for c in r[reports[0]]['cases'])
assert len(r[reports[1]]['cases'])==3 and r[reports[2]]['tests_run']==100
assert r[reports[3]]['batch_squads']==8 and r[reports[4]]['total_damage']==692308676 and r[reports[4]]['positive_frames']==301
files=reports+['research/save-enemy-fanout-native-stage.py','research/checkpoint_receipts.py','research/benchmark-gpu-fanout.py','research/verify-enemy-fields-normal-witness.py','research/enemy-fields-api-fixture.json','app/enemy_recipient_specs.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/enemy_fanout_cases.py','scripts/verify-enemy-fanout-detail.py','scripts/verify-common-runtime-unit.py','tests/test_enemy_recipient_runtime.py']
print(save_checkpoint('research/enemy-fanout-native-stage.json','research/ports/v78-enemy-fanout-native-stage',dict(passed=True,objective_complete=False,abi='detail_enemy_fanout_v78',workspace_bytes=1274400,gpu_fanout_connected=True,portable_verified=False,normal_summon_admission=False),files))
