"""Native functional baseline for autonomous reload production, before indexing."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,checked_receipts,save_checkpoint
reports=['research/mode-inputs-'+name+'.json' for name in ('native','native-unit','coverage')]
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==7 and r[reports[1]]['tests_run']==81 and r[reports[2]]['supported']==187
assert r[reports[2]]['existing_programs_identical']==186 and r[reports[2]]['old_weapon_words_identical']
assert all(row['cpu_mode_shots']==row['gpu_mode_shots'] and (row['gpu_mode_shots']>0)==row['mode_expected'] for row in r[reports[0]]['cases'])
assert read('app/detail_effects-sm86.json')['abi']=='detail_mode_inputs_v69'
files=['app/engine_worker.py','app/detail_gpu.py','app/effect_spec.py','app/weapon_mode_runtime.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json',
    'web/app.js','web/index.html','scripts/verify-common-runtime-unit.py','scripts/verify-mode-inputs-detail.py','tests/test_mode_input_policy.py',
    'research/verify-mode-inputs-coverage.py','research/save-mode-inputs-stage.py','research/checkpoint_receipts.py']
c=dict(passed=True,native_stage_only=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base='research/ports/v68-mode-commands-verified',reports=reports,abi='detail_mode_inputs_v69',instruction_width=344,character_width=169,
    autonomous_manual_mode_input_connected=True,cpu_reload_entry_initialization_fixed=True,source_rules_verified_in_game=False,standard_compile_supported=187,
    next='Freeze actual mode calculation latency, then replace the per-frame effect scan with the existing event19 index. Portable artifact and normal API/UI validation remain pending.')
print(json.dumps(save_checkpoint('research/mode-inputs-native-stage.json','research/ports/v69-mode-inputs-native-stage',c,files+reports)))
