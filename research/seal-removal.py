"""Seal common scoped removal, input views and bounded verified-source timing."""
import hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='9047790eea544c91df2124a05a4a7f65d066aca9';OLD='272ed619c7504a603edd1f8e9d53ad51ad34a999'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,d):(P/(n+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=load('portable-combat-metal');w=load('windows-portable-combat-v43');roster=load('portable-roster-battles-metal');api=load('portable-api-metal');audit=load('portable-catalog-readiness');bench=load('portable-definition-view-benchmark');parity=load('portable-definition-view-parity');gates=load('portable-removal-global-gates');transfer=load('portable-removal-transfer-completed');unit=load('portable-removal-unit-tests')
assert m['passed'] and m['gpu_execution_verified'] and len(m['cases'])==1092 and len(m['rejected_cases'])==195
assert len(m['removal_cpu_regressions'])==28 and len(m['weapon_cpu_regressions'])==87
assert subprocess.check_output(['git','show',SOURCE+':research/portable-combat-metal.json'],cwd=R)==(P/'portable-combat-metal.json').read_bytes()
keys=['source_sha256','input_sha256','output_sha256','validation_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
for key in keys:assert w[key]==m[key],key
assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
assert w['passed'] and w['gpu_execution_verified'] and w['backend']=='cuda' and w['execution']['commit']==SOURCE
assert w['execution']['exit_code']==0 and not w['execution']['timed_out'] and w['execution']['below_normal_priority'] and w['execution']['timeout_seconds']==120
assert w['postcheck']['remaining_verification_processes']==0
for key in ('head','status'):assert w['postcheck']['original_'+key+'_after']==w['execution']['original_'+key+'_before']
assert gates['passed'] and gates['complete'] and len(gates['gates'])==15
assert transfer['passed'] and transfer['windows_execution_and_transfer_terminal'] and transfer['parts']==22
assert roster['passed'] and len(roster['cases'])==58 and all(c['passed'] and not c['differences'] for c in roster['cases'])
assert audit['catalog_characters']==203 and audit['own_effect_preflight_passed']==29 and audit['full_character_verified']==0
assert api['passed'] and len(api['removal_execution'])==4 and unit['passed'] and unit['tests']==118
for name in ('input','scalar','out'):
 c=load('portable-definition-'+name+'-metal');assert c['passed'] and c['decoded_fields']==55 and c['records']==1024 and c['word_values']==62464
for key in ('source_sha256','input_sha256','output_sha256'):assert w['definition_scalar_codec'][key]==load('portable-definition-scalar-metal')[key]
assert parity['passed'] and parity['byte_identical_outputs'] and parity['positive_inputs']==1092 and parity['production_source_sha256']==m['source_sha256']
assert bench['passed'] and bench['all_output_hashes_equal'] and bench['production_source_sha256']==m['source_sha256']
assert bench['timing_order']['windows_execution_and_transfer_terminal'] and not bench['timing_order']['verification_processes']
for key,h in m['source_sha256'].items():assert sha(R/key)==h,key
for key,h in m['validation_sha256'].items():assert sha(R/key)==h,key
for folder in ('app','scripts'):
 for file in (R/folder).glob('*.py'):assert roster['validation_sha256'][file.relative_to(R).as_posix()]==sha(file),file
old=json.loads(subprocess.check_output(['git','show',OLD+':research/portable-roster-battles-metal.json'],cwd=R));current={(c['character'],c['grown'],c['duration']):c for c in roster['cases']}
for c in old['cases']:
 d=current[c['character'],c['grown'],c['duration']];assert d['gpu_result']==c['gpu_result'];assert d['native_reference']==c['native_reference']
existing=load('portable-removal-existing-parity');assert existing['passed'] and existing['unchanged_decoded_full_states']==1059
existing.update(unchanged_real_profiles=58,profile_baseline_proof_commit=OLD,profile_report_sha256=sha(P/'portable-roster-battles-metal.json'));save('portable-removal-existing-parity',existing)
save('portable-combat-cuda',dict(w,summary_only=True,summary_source='windows-portable-combat-v43.json',scope=m['scope']))
cp=load('portable-combat-v41-checkpoint')
cp.update(wire_abi='0x50455659',verified_commit=SOURCE,source_provenance=dict(fixed_shared_source_commit=SOURCE,metal_core_report_source_commit=SOURCE,windows_source_commit=SOURCE),previous_checkpoint=dict(report='portable-combat-v41-checkpoint.json',proof_commit=OLD),positive_cases=1092,rejections=195,batched_inputs=1287,source_sha256=m['source_sha256'],input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],validation_sha256=m['validation_sha256'],unit_tests=118,regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')},missing_families=audit['missing_families'],windows_report='windows-portable-combat-v43.json',windows_execution=w['execution'],windows_postcheck=w['postcheck'],cuda_comparison={k:True for k in keys},generated_source_comparison='portable-generated-v43-comparison.json',validation_receipt='portable-removal-validation.json',existing_parity='portable-removal-existing-parity.json',removal_cases=29,removal_native_cpu_cases=28,removal_api_cases=4,removal_notice_capacity=4096,removal_notice_words=2048,removal_notice_gpu_owned=True,definition_input_views=True,definition_scalar_accessors=55,definition_record_out_abi=True,definition_private_nominal_bytes_removed=63488,definition_codec_records=1024,definition_codec_fields=55,definition_scalar_to_full_record_timing_ratio=bench['scalar_to_record_ratio'],definition_efficiency_scope=bench['scope'],normal_ui_connected=False,normal_ui_backend='cpu',all_characters_supported=False,full_goal_complete=False,full_character_verified=0,next_work=['Connect remaining lifecycle/recipient/world and effect families across all 203 characters','Keep unchanged CPU reference differences explicit; certify every character variant before normal UI Metal'])
save('portable-combat-checkpoint',cp)
r=load('portable-removal-work-in-progress');r.update(stage='scoped-removal-and-definition-views-verified-on-both-gpus',passed=True,current_source_uncommitted=False,previous_stable_source_commit=r.get('previous_stable_source_commit',r['stable_source_commit']),previous_stable_proof_commit=r.get('previous_stable_proof_commit',r['stable_proof_commit']),stable_source_commit=SOURCE,stable_proof_commit=None,validation_receipt='portable-removal-validation.json',windows_current_candidate_verified=True,windows_gpu_runs_this_phase=1,efficiency_measurement_completed=True,live_handles={},definition_timing_ratio=bench['scalar_to_record_ratio'],next_actions=cp['next_work']);save('portable-removal-work-in-progress',r)
reports=['portable-combat-metal','portable-combat-cuda','windows-portable-combat-v43','portable-roster-battles-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-api-metal','portable-metal-pipeline-lock','portable-numeric-metal','portable-probe-metal','portable-catalog-readiness','portable-removal-unit-tests','portable-removal-queue-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-existing-parity','portable-generated-v43-comparison','portable-removal-global-gates','portable-removal-transfer-completed','portable-removal-timing-order','portable-definition-view-parity','portable-definition-view-benchmark','portable-removal-work-in-progress','portable-combat-checkpoint']
for n in reports:
 d=load(n)
 if n!='portable-catalog-readiness':assert d['passed'] if 'passed' in d else d.get('metal_verified'),n
save('portable-removal-validation',dict(passed=True,full_goal_complete=False,full_character_verified=0,source_commit=SOURCE,windows_gpu_runs_of_bounded_wrapper=1,windows_elapsed_seconds=w['execution']['elapsed_seconds'],positive_cases=1092,rejections=195,native_removal_cases=28,real_profiles=58,unit_tests=118,unchanged_prior_full_states=1059,unchanged_real_profiles=58,all_generated_normalized_sources_equal=True,efficiency_measurement_completed=True,definition_scalar_to_record_ratio=bench['scalar_to_record_ratio'],definition_private_nominal_bytes_removed=63488,peak_gpu_memory_measured=False,scope='Shared scoped removal and immutable definition views, bounded input-view efficiency; full catalog and all variants remain uncertified',artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},tool_sha256={str(p.relative_to(R)):sha(p) for p in (P/'benchmark-definition-views.py',P/'verify-definition-input.py')}))
print('Sealed scoped removal and definition views:',len(reports),'artifacts; full goal incomplete')
