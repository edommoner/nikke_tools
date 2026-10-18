"""Freeze sparse recipient storage before static-world descriptor folding."""
from checkpoint_receipts import checked_receipts,save_checkpoint
reports=['research/enemy-fields-'+n+'.json' for n in ('native','unit-stage','order-native','owned-api-stage','normal-before','before-api')]
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==3 and all(c['workspace_bytes']==1225248 for c in r[reports[0]]['cases'])
assert r[reports[1]]['tests_run']==98 and len(r[reports[2]]['cases'])==25
assert r[reports[3]]['pure_gpu_and_verified_and_cpu_equal'] and r[reports[3]]['mode_policy_roundtrip']['passed']
assert r[reports[4]]['positive_frames']>0 and r[reports[4]]['max_modifier']>0 and r[reports[5]]['candidates']==8
files=reports+['research/save-enemy-fields-native-stage.py','research/checkpoint_receipts.py','research/verify-enemy-fields-normal-witness.py','research/enemy-fields-api-fixture.json','research/benchmark-normal-search.mjs',
    'app/enemy_recipient_specs.py','app/enemy_recipient_runtime.py','app/target_context_runtime.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json',
    'scripts/build-detail-native.py','scripts/build-detail-ptx.py','scripts/enemy_recipient_cases.py','scripts/verify-enemy-fields-detail.py','tests/test_enemy_recipient_runtime.py']
print(save_checkpoint('research/enemy-fields-native-stage.json','research/ports/v76-enemy-fields-native-stage',dict(passed=True,objective_complete=False,abi='detail_enemy_fields_v76',workspace_bytes=1225248,state_growth_bytes=6144,target_cases=3,lightweight_methods=98,existing_ordering_cases=25,normal_owned_api=True,positive_raw_field_frames=r[reports[4]]['positive_frames'],portable_verified=False,normal_summon_admission=False),files))
