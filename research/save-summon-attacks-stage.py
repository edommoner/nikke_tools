"""Freeze shared source attacks before skipping frames with no due work."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import checked_receipts,save_checkpoint
reports=['research/summon-attacks-'+n+'.json' for n in ('native','native-unit','coverage','initial-controls')];r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==12 and r[reports[1]]['tests_run']==86
assert r[reports[2]]['supported']==r[reports[2]]['existing_programs_identical']==187 and r[reports[3]]['tests_run']==7
files=['app/detail_gpu.py','app/detail_boss.py','app/engine_worker.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','tests/test_world_actor_runtime.py','scripts/summon_source_cases.py','scripts/verify-summon-sources-detail.py','research/save-summon-attacks-stage.py','research/verify-summon-attacks-coverage.py','research/checkpoint_receipts.py']
c=dict(passed=True,native_stage_only=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base='research/ports/v71-summon-sources-verified',reports=reports,abi='detail_summon_attacks_v72',source_attacks_connected=True,actor_first_order_verified=True,time0_single_frame_verified=True,normal_summon_admission=False,autonomous_target_routing_connected=False,autonomous_multi_hit_connected=False,standard_compile_supported=187,next='Measure actual source schedule/HP execution, then skip actors when no shot is due or the schedule is exhausted. Portable backend and final API/mixed regression controls remain pending.')
print(json.dumps(save_checkpoint('research/summon-attacks-native-stage.json','research/ports/v72-summon-attacks-native-stage',c,files+reports)))
