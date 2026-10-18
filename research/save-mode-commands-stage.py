"""Native functional baseline before optimizing the shared ammunition queue."""
import json
from datetime import datetime,timezone
from checkpoint_receipts import ROOT,read,sha,checked_receipts,save_checkpoint
reports=['research/mode-commands-'+name+'.json' for name in ('native','native-unit','coverage')]
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==4 and r[reports[1]]['tests_run']==78
assert r[reports[2]]['supported']==r[reports[2]]['existing_programs_identical']==186
assert read('app/detail_effects-sm86.json')['abi']=='detail_mode_commands_v68'
files=['app/weapon_mode_specs.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','tests/test_weapon_mode_specs.py',
    'scripts/verify-mode-commands-detail.py','scripts/verify-common-runtime-unit.py','research/verify-mode-commands-coverage.py','research/save-mode-commands-stage.py','research/checkpoint_receipts.py']
c=dict(passed=True,native_stage_only=True,objective_complete=False,generated_at=datetime.now(timezone.utc).isoformat(),archive_base='research/ports/v67-named-allies-verified',reports=reports,abi='detail_mode_commands_v68',instruction_width=344,workspace_bytes=1216840,
    independent_command_cases=4,autonomous_manual_reload_input_connected=False,character_admission_changed=False,standard_compile_supported=186,existing_programs_identical=186,
    next='Measure the same notice queue workload, then optimize only after this baseline. Connect manual reload production and real raw mode activation before admitting the character. Portable artifact generation and normal-path validation are still pending.')
print(json.dumps(save_checkpoint('research/mode-commands-native-stage.json','research/ports/v68-mode-commands-native-stage',c,files+reports)))
