"""Preserve per-recipient semantics before extracting the reusable executor."""
from checkpoint_receipts import checked_receipts,save_checkpoint
reports=['research/enemy-fanout-'+n+'.json' for n in ('reference-stage','unit-stage','before')]
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'][0]['observations'])==14 and r[reports[1]]['tests_run']==102
files=reports+['research/save-enemy-fanout-cpu-stage.py','research/checkpoint_receipts.py','research/benchmark-enemy-fanout.py','app/enemy_recipient_runtime.py','app/reference_rewrite.py','scripts/audit-effect-runtime.py','scripts/verify-common-runtime-unit.py','scripts/verify-enemy-fanout-reference.py','scripts/enemy_fanout_cases.py','tests/test_enemy_recipient_runtime.py']
print(save_checkpoint('research/enemy-fanout-cpu-stage.json','research/ports/v77-enemy-fanout-cpu-stage',dict(passed=True,objective_complete=False,cpu_only=True,abi='detail_enemy_fields_v76',gpu_fanout_connected=False,normal_summon_admission=False),files))
