"""Preserve shared receiver mutations before filtering unrelated entries early."""
from checkpoint_receipts import checked_receipts,save_checkpoint
reports=['research/enemy-mutations-native.json','research/mutations-fanout-native-stage.json','research/enemy-mutations-unit-stage.json','research/gpu-mutations-before.json','research/mutations-normal-before.json']
r=checked_receipts(reports)
assert r[reports[0]]['cases'][0]['observations']==22 and r[reports[0]]['cases'][0]['workspace_bytes']==1258016
assert len(r[reports[1]]['cases'])==4 and r[reports[2]]['tests_run']==103
assert r[reports[3]]['batch_squads']==8 and r[reports[4]]['total_damage']==692308676 and r[reports[4]]['positive_frames']==301
files=reports+['research/save-enemy-mutations-native-stage.py','research/checkpoint_receipts.py','research/benchmark-gpu-mutations.py','research/verify-enemy-fields-normal-witness.py','research/enemy-fields-api-fixture.json','app/enemy_recipient_runtime.py','app/enemy_recipient_specs.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/enemy_mutation_cases.py','scripts/verify-enemy-mutations-detail.py','scripts/verify-common-runtime-unit.py','tests/test_enemy_recipient_runtime.py']
print(save_checkpoint('research/enemy-mutations-native-stage.json','research/ports/v79-enemy-mutations-native-stage',dict(passed=True,objective_complete=False,abi='detail_enemy_mutations_v79',workspace_bytes=1258016,portable_verified=False,normal_summon_admission=False),files))
