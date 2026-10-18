"""Freeze the functional native baseline before measuring retained-scope cost."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,checked_receipts,save_checkpoint
reports=['research/target-scopes-native.json','research/target-scopes-native-unit.json','research/target-scopes-coverage.json','research/runtime-wiring.json']
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==10 and r[reports[1]]['tests_run']==72
assert r[reports[2]]['supported']==r[reports[2]]['existing_programs_identical']==185
files=['app/world_actor_runtime.py','app/impact_runtime.py','app/attack_group_runtime.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json',
    'tests/test_world_actor_runtime.py','tests/test_impact_runtime.py','tests/test_attack_group_runtime.py','scripts/verify-common-runtime-unit.py','scripts/verify-attack-groups-detail.py','research/save-target-scopes-stage.py','research/checkpoint_receipts.py']
c=dict(passed=True,native_stage_only=True,objective_complete=False,archive_base='research/ports/v66-attack-groups-foundation-verified',
    generated_at=datetime.now(timezone.utc).isoformat(),reports=reports,abi='detail_target_scopes_v67',workspace_bytes=1216840,
    retained_storage_verified=True,cpu_add_landing_bridge_verified=True,autonomous_producer_connected=False,matched_target_effect_routing_connected=False,game_rules_verified=False)
print(json.dumps(save_checkpoint('research/target-scopes-native-stage.json','research/ports/v67-target-scopes-native-stage',c,files+reports)))
