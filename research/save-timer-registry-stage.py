from checkpoint_receipts import ROOT,checked_receipts,save_checkpoint
from shutil import copy2
copy2(ROOT/'research/timer-registry-native.json',ROOT/'research/timer-registry-native-stage.json')
reports=['research/timer-registry-'+n+'.json' for n in ('native-stage','instant-stage','staged-stage','unit-stage','before','coverage')]
r=checked_receipts(reports)
assert len(r[reports[0]]['cases'])==7 and len(r[reports[1]]['cases'])==6 and len(r[reports[2]]['cases'])==9
assert r[reports[3]]['tests_run']==110 and r[reports[5]]['existing_programs_identical']==187
files=reports+['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/periodic_target_runtime.py','app/timer_registry_runtime.py','scripts/timer_registry_cases.py','scripts/verify-timer-registry-detail.py','scripts/verify-common-runtime-unit.py','tests/test_timer_registry_runtime.py','research/benchmark-periodic-targets.py','research/benchmark-periodic-normal.py','research/save-timer-registry-stage.py']
print(save_checkpoint('research/timer-registry-native-stage.json.receipt','research/ports/v81-timer-registry-native-stage',dict(passed=True,objective_complete=False,abi='detail_timer_registry_v81',workspace_bytes=1260136,shared_cases=7,existing_instant_cases=6,existing_staged_cases=9,lightweight_methods=110,existing_programs_identical=187),files))
