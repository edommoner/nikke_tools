"""Freeze explicit target context before skipping uninterested dispatch work."""
from checkpoint_receipts import checked_receipts,save_checkpoint
reports=['research/target-context-'+n+'.json' for n in ('native','native-stage-unit','order-native','coverage','before-api')]
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==1 and r[reports[0]]['cases'][0]['workspace_bytes']==1219104
assert r[reports[1]]['tests_run']==92 and len(r[reports[2]]['cases'])==25
assert r[reports[3]]['supported']==r[reports[3]]['existing_programs_identical']==187
assert r[reports[4]]['candidates']==8 and r[reports[4]]['cache_hits']==0
files=reports+['research/save-target-context-stage.py','research/checkpoint_receipts.py','research/benchmark-normal-search.mjs','research/world-bindings-api-fixture.json',
    'app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/world_condition_specs.py','app/target_context_runtime.py','app/effect_runtime.py','app/impact_specs.py','app/effect_spec.py',
    'scripts/verify-target-context-detail.py','scripts/verify-common-runtime-unit.py','tests/test_target_context_runtime.py','tests/test_world_condition_specs.py']
print(save_checkpoint('research/target-context-native-stage.json','research/ports/v74-target-context-native-stage',
    dict(passed=True,objective_complete=False,abi='detail_target_context_v74',target_context_predicates_verified=True,counter_completion_target_connected=True,normal_summon_admission=False,
        workspace_bytes=1219104,state_growth_bytes=16,source_cases=1,lightweight_methods=92,existing_ordering_cases=25,portable_verified=False),files))
