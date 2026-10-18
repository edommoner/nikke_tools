"""Freeze functional scanning lookup before trying direct canonical lookup."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import checked_receipts,save_checkpoint
reports=['research/world-bindings-'+n+'.json' for n in ('native','native-unit','coverage')]
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==5 and r[reports[1]]['tests_run']==83
assert r[reports[2]]['supported']==r[reports[2]]['existing_programs_identical']==187
files=['app/world_actor_specs.py','app/world_actor_runtime.py','app/detail_boss.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','tests/test_world_actor_runtime.py','scripts/verify-world-bindings-detail.py','research/verify-world-bindings-coverage.py','research/save-world-bindings-stage.py','research/checkpoint_receipts.py']
c=dict(passed=True,native_stage_only=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base='research/ports/v69-mode-inputs-verified',reports=reports,abi='detail_world_bindings_v70',configured_world_bindings_shared=True,live_sources=['body','fixed_part'],summon_live_pool_connected=False,autonomous_multi_hit_connected=False,standard_compile_supported=187,character_admission_changed=False,next='Measure actual normal-path latency, then try canonical direct lookup. Portable backend, normal API and mixed-world regressions remain pending.')
print(json.dumps(save_checkpoint('research/world-bindings-native-stage.json','research/ports/v70-world-bindings-native-stage',c,files+reports)))
