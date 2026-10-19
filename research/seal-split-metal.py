"""Mac-only progress checkpoint; explicitly leaves CUDA and open wire work pending."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='d12b365'
load=lambda n:json.loads((P/(n+'.json')).read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=subprocess.check_output(['git','rev-parse',SOURCE],cwd=R,text=True).strip()
subprocess.run(['git','diff','--exit-code',source,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
m=load('portable-combat-metal');g=load('portable-split-global-gates');r=load('portable-roster-battles-metal');api=load('portable-api-metal');prior=load('portable-split-existing-metal-parity');audit=load('portable-catalog-readiness');probe=load('portable-instant-list-admission-probe-metal')
assert m['passed'] and len(m['cases'])==1479 and len(m['rejected_cases'])==294 and len(m['protection_cpu_regressions'])==103
assert g['passed'] and g['complete'] and len(g['gates'])==25 and g['source_commit']==source and all(x['source_commit']==source for x in g['gates'])
assert r['passed'] and len(r['cases'])==82 and api['passed'] and len(api['split_execution'])==6
assert prior['passed'] and prior['prior_inputs']==1709 and prior['all_old_output_words_equal'] and prior['all_added_old_output_tail_words_zero']
assert audit['own_effect_preflight_passed']==41 and audit['full_character_verified']==0
for key in ('source_sha256','validation_sha256'):
 for p,h in m[key].items():assert sha(R/p)==h,p
for p,h in m['source_sha256'].items():assert hashlib.sha256(subprocess.check_output(['git','show',source+':'+p],cwd=R)).hexdigest()==h,p
old=json.loads(subprocess.check_output(['git','show','b8ae1c7:research/portable-roster-battles-metal.json'],cwd=R));strip=lambda c:{k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'};current={(c['character'],c['grown']):strip(c) for c in r['cases']}
for c in old['cases']:assert current[c['character'],c['grown']]==strip(c)
units={}
for name,count in {'unit':166,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
 row=next(x for x in g['gates'] if x['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');units[name]=dict(tests=count,output=text)
(P/'portable-split-unit-tests.json').write_text(json.dumps(dict(passed=True,groups=units),indent=2)+'\n')
(P/'portable-split-roster-parity.json').write_text(json.dumps(dict(passed=True,old_profiles_preserved=74,current_profiles=82,excluded_fields=['cpu_reference_wall_seconds']),indent=2)+'\n')
reports=['portable-combat-metal','portable-split-global-gates','portable-split-existing-metal-parity','portable-split-native','portable-split-metal','portable-protection-native','portable-protection-metal','portable-split-storage','portable-split-trace-failure','portable-split-oracle-mask-correction','portable-split-unit-tests','portable-split-roster-parity','portable-instant-list-admission-probe-metal','portable-roster-battles-metal','portable-api-metal','portable-catalog-readiness','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock','portable-duration-extend-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-queue-metal','portable-stack-numeric-metal','portable-stack-notices-metal']
tools=[P/n for n in ('build-split-cases.py','verify-protection.py','verify-split-regression.py','run-split-gates.py','verify-split-storage.py','split-terminal-check.py','benchmark-split.py','seal-split.py','probe-instant-list.py','seal-split-metal.py')]
docs=[R/'docs'/n for n in ('portable-split.md','mac-handoff.md','mac-migration.md','portable-combat-runtime.md')]
receipt=dict(passed=True,scope='Mac accepted-input contract checkpoint only; not a full-stage or full-goal completion',source_commit=source,positive_cases=1479,rejections=294,batched_inputs=1773,unit_tests=166,native_split_cases=46,mac_gates=25,real_profiles=82,old_profiles_preserved=74,normal_ui_backend='cpu',full_character_verified=0,full_goal_complete=False,cuda_current_result_confirmed=False,windows_request=dict(version='v59',thread_id='01a140bc-5f3b-7661-b720-50c945596eaa',host='remote-control:env_e_6ac12920046c8331afb50b0234aeba48',turn_id='01a15680-1bf6-7910-9924-0040c5046a0f',status='Result/transfer terminal unconfirmed after host became unavailable; do not restart from this observation alone'),efficiency_evaluated=False,open_wire_boundary=dict(report='portable-instant-list-admission-probe-metal.json',normal_host_admission_rejects=True,gpu_admitted=probe['gpu_admitted_unported_instant_list'],expected_hp=probe['expected_hp'],actual_hp=probe['actual_hp'],resolved=probe['full_instant_list_supported'],next_work='Connect the ordered instantaneous delivery executor, or reject the unsupported raw wire form before efficiency work'),artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},tool_sha256={str(p.relative_to(R)):sha(p) for p in tools},documentation_sha256={str(p.relative_to(R)):sha(p) for p in docs})
(P/'portable-split-metal-validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print('Mac25 gates sealed; CUDA and instant-list boundary remain explicitly pending')
