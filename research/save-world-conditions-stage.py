"""Freeze dynamic predicates before immutable-world specialization."""
from checkpoint_receipts import checked_receipts,save_checkpoint
reports=['research/world-conditions-native.json','research/world-conditions-native-stage-unit.json','research/world-conditions-before-api.json']
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==2 and r[reports[1]]['tests_run']==89
assert r[reports[2]]['candidates']==8 and r[reports[2]]['cache_hits']==0
files=reports+['research/save-world-conditions-stage.py','research/checkpoint_receipts.py','research/benchmark-normal-search.mjs','research/world-conditions-api-fixture.json',
    'app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/world_condition_specs.py',
    'scripts/verify-world-conditions-detail.py','scripts/verify-summon-sources-detail.py','scripts/verify-common-runtime-unit.py','scripts/build-detail-native.py','scripts/build-detail-ptx.py','tests/test_world_condition_specs.py']
print(save_checkpoint('research/world-conditions-native-stage.json','research/ports/v73-world-conditions-native-stage',
    dict(passed=True,objective_complete=False,abi='detail_world_conditions_v73',dynamic_count_predicates_verified=True,normal_summon_admission=False,
        existing_snapshot_reused=True,state_growth_bytes=0,source_cases=2,lightweight_methods=89,portable_verified=False),files))
