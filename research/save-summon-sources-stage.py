"""Freeze source lifecycle and pool receipts before lookup optimization."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import checked_receipts,save_checkpoint
reports=['research/summon-sources-'+n+'.json' for n in ('native','native-unit','coverage')];r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==7 and r[reports[1]]['tests_run']==85
assert r[reports[2]]['supported']==r[reports[2]]['existing_programs_identical']==187
files=['app/detail_gpu.py','app/detail_boss.py','app/detail_effects.cu','app/world_actor_specs.py','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','tests/test_world_actor_runtime.py','scripts/summon_source_cases.py','scripts/verify-summon-sources-detail.py','research/save-summon-sources-stage.py','research/verify-summon-sources-coverage.py','research/checkpoint_receipts.py']
c=dict(passed=True,native_stage_only=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base='research/ports/v70-world-bindings-verified',reports=reports,abi='detail_summon_sources_v71',passive_summon_source_verified=True,normal_summon_admission=False,attached_summon_attacks_connected=False,autonomous_target_routing_connected=False,autonomous_multi_hit_connected=False,standard_compile_supported=187,next='Measure source-pool lookup workload, then reuse canonical contiguous add identities. Portable backend and existing full battle/API controls remain pending.')
print(json.dumps(save_checkpoint('research/summon-sources-native-stage.json','research/ports/v71-summon-sources-native-stage',c,files+reports)))
