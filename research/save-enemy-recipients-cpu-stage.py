"""Freeze the actual CPU recipient reference before cache optimization."""
from checkpoint_receipts import checked_receipts,save_checkpoint,read,sha
reports=['research/enemy-recipients-reference-before.json','research/enemy-recipients-unit-before.json','research/enemy-recipient-queries-before.json']
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'][0]['observations'])==18 and r[reports[1]]['tests_run']==98
prior=read('research/target-context-checkpoint.json')
assert all(sha(name)==prior['source_sha256'][name] for name in ('app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json'))
files=reports+['research/save-enemy-recipients-cpu-stage.py','research/checkpoint_receipts.py','research/benchmark-enemy-recipient-queries.py',
    'app/enemy_recipient_specs.py','app/enemy_recipient_runtime.py','app/effect_spec.py','app/lifecycle_specs.py','app/impact_specs.py',
    'scripts/enemy_recipient_cases.py','scripts/verify-enemy-recipients-reference.py','scripts/verify-common-runtime-unit.py','tests/test_enemy_recipient_runtime.py','tests/test_target_context_runtime.py']
print(save_checkpoint('research/enemy-recipients-cpu-stage.json','research/ports/v75-enemy-recipients-cpu-stage',dict(passed=True,objective_complete=False,cpu_only=True,observations=18,lightweight_methods=98,gpu_storage_connected=False,normal_summon_admission=False,gpu_abi='detail_target_context_v74',gpu_binaries_changed=False),files))
