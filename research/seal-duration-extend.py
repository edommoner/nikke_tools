"""Seal final independent enemy lifetimes, infinity identity and guarded fast path."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='b0f1cf335e61e3b61c820823b0c5578b176ebdcd';BASE='43f43a54535992d6992e0b3042c99c2e6c809bd4';OLD='dcae794ceebe0043529c5289eb430ee374d43f12'
def load(n):return json.loads((P/(n+'.json')).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,r):(P/(n+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
m=load('portable-combat-metal');w=load('windows-portable-combat-v45');baseline=load('windows-portable-combat-v44');gates=load('portable-duration-extend-global-gates');roster=load('portable-roster-battles-metal');api=load('portable-api-metal');audit=load('portable-catalog-readiness');native=load('portable-duration-extend-metal');bench=load('portable-enemy-fanout-benchmark');parity=load('portable-enemy-fanout-parity')
assert m['passed'] and m['gpu_execution_verified'] and len(m['cases'])==1131 and len(m['rejected_cases'])==206
assert len(m['duration_extend_cpu_regressions'])==39 and native['passed'] and len(native['cases'])==39
assert subprocess.check_output(['git','show',SOURCE+':research/portable-combat-metal.json'],cwd=R)==(P/'portable-combat-metal.json').read_bytes()
keys=['source_sha256','input_sha256','output_sha256','validation_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
for k in keys:assert w[k]==m[k],k
assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
for report,commit in [(w,SOURCE),(baseline,BASE)]:
 assert report['passed'] and report['gpu_execution_verified'] and report['execution']['commit']==commit
 assert report['execution']['exit_code']==0 and not report['execution']['timed_out'] and report['execution']['below_normal_priority'] and report['execution']['timeout_seconds']==120
 assert report['postcheck']['remaining_verification_processes']==0
 for k in ('head','status'):assert report['postcheck']['original_'+k+'_after']==report['execution']['original_'+k+'_before']
assert gates['passed'] and gates['complete'] and len(gates['gates'])==16
assert roster['passed'] and len(roster['cases'])==58 and all(c['passed'] and not c['differences'] for c in roster['cases'])
assert api['passed'] and len(api['duration_extend_execution'])==4
assert audit['catalog_characters']==203 and audit['own_effect_preflight_passed']==29 and audit['full_character_verified']==0 and audit['missing_families']['effect_lifecycle']==81
for k,h in m['source_sha256'].items():assert sha(R/k)==h,k
for k,h in m['validation_sha256'].items():assert sha(R/k)==h,k
for folder in ('app','scripts'):
 for p in (R/folder).glob('*.py'):assert roster['validation_sha256'][p.relative_to(R).as_posix()]==sha(p),p
assert bench['passed'] and parity['passed'] and parity['positive_inputs']==1131
assert bench['timing_order']['windows_execution_and_transfer_terminal'] and not bench['timing_order']['verification_processes']
prefix='research/portable-build/enemy-fanout-single/'
optimized={k[len(prefix):]:h for k,h in parity['variants']['single']['source_sha256'].items() if k.startswith(prefix+'gpu/')}
assert optimized==m['source_sha256'],'Promoted shader differs from the exact measured candidate'
for report in ('portable-duration-extend-transfer-completed','portable-duration-extend-optimized-transfer-completed'):
 t=load(report);assert t['passed'] and t['windows_execution_and_transfer_terminal'] and t['thread_status']=='idle' and t['turn_status']=='completed'
old=load('portable-combat-v43-metal');a={c['name']:v for c,v in zip(old['cases'],old['results'])};b={c['name']:v for c,v in zip(m['cases'],m['results'])};same=[n for n in a if a[n]==b[n]];changed=[n for n in a if a[n]!=b[n]]
assert all(a[n]['queries']==b[n]['queries'] for n in a)
old_profiles=json.loads(subprocess.check_output(['git','show',OLD+':research/portable-roster-battles-metal.json'],cwd=R));profiles={(c['character'],c['grown'],c['duration']):c for c in roster['cases']}
def prior_fields(x):
 if isinstance(x,dict):return {k:prior_fields(v) for k,v in x.items() if k!='enemy_generation'}
 if isinstance(x,list):return [prior_fields(v) for v in x]
 return x
for c in old_profiles['cases']:
 current=profiles[c['character'],c['grown'],c['duration']];assert prior_fields(current['gpu_result'])==c['gpu_result'];assert current['native_reference']==c['native_reference']
save('portable-duration-extend-existing-parity',dict(passed=True,baseline_source_commit='9047790eea544c91df2124a05a4a7f65d066aca9',baseline_proof_commit=OLD,unchanged_all_queries=len(a),unchanged_complete_readbacks=len(same),changed_physical_enemy_state_cases=changed,unchanged_real_profiles=58,real_profile_comparison='Every prior field retained; new enemy_generation metadata is compared separately against native generation-aware fixtures',scope='Every old query and every original real-profile result; enemy resident/generation representation and actual frame-depth differences remain explicit',artifact_sha256={str(p.relative_to(R)):sha(p) for p in [P/'portable-combat-metal.json',P/'portable-combat-v43-metal.json',P/'portable-roster-battles-metal.json']}))
save('portable-combat-cuda',dict(w,summary_only=True,summary_source='windows-portable-combat-v45.json',scope=m['scope']))
cp=load('portable-combat-v43-checkpoint');cp.update(wire_abi='0x50455660',verified_commit=SOURCE,source_provenance=dict(fixed_shared_source_commit=SOURCE,metal_core_report_source_commit=SOURCE,windows_source_commit=SOURCE,pre_optimization_source_commit=BASE),previous_checkpoint=dict(report='portable-combat-v43-checkpoint.json',proof_commit=OLD),positive_cases=1131,rejections=206,batched_inputs=1337,source_sha256=m['source_sha256'],input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],validation_sha256=m['validation_sha256'],unit_tests=127,native_runtime_tests=15,regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')},missing_families=audit['missing_families'],windows_checks_this_stage=2,windows_report='windows-portable-combat-v45.json',windows_execution=w['execution'],windows_postcheck=w['postcheck'],windows_baseline_execution=baseline['execution'],cuda_comparison={k:True for k in keys},generated_source_comparison='portable-generated-v45-comparison.json',validation_receipt='portable-duration-extend-validation.json',existing_parity='portable-duration-extend-existing-parity.json',duration_extend_cases=39,duration_extend_api_cases=4,enemy_resident_per_recipient=True,enemy_generation_capture=True,lifetime_true_software_binary64_infinity=True,public_lifetime_projection='signed infinity to signed 1e30; finite values unchanged',single_receiver_fast_path=True,single_receiver_fast_path_requires_no_pending_hp=True,enemy_fanout_timing_scope=bench['scope'],enemy_fanout_timing={k:dict(median_gpu_seconds=v['median_gpu_seconds'],ratio=v['single_to_queued_ratio']) for k,v in bench['workloads'].items()},normal_ui_connected=False,normal_ui_backend='cpu',all_characters_supported=False,full_goal_complete=False,full_character_verified=0,next_work=['Connect remaining lifecycle/recipient/world and effect families across all 203 characters','Certify every character variant with actual CPU/GPU evidence before normal UI Metal'])
save('portable-combat-checkpoint',cp)
r=load('portable-duration-extend-work-in-progress');r.update(passed=True,stage='duration-extension-independent-enemy-cells-and-guarded-fast-path-verified',source_commit=SOURCE,windows_current_source_verified=True,optimized_windows_verified=True,optimized_windows_runs=1,windows_runs_this_phase=2,optimized_global_gates_completed=True,efficiency_measurement_completed=True,live_handles={},validation_receipt='portable-duration-extend-validation.json',next_actions=cp['next_work']);save('portable-duration-extend-work-in-progress',r)
reports=['portable-combat-metal','portable-combat-cuda','windows-portable-combat-v44','windows-portable-combat-v45','portable-roster-battles-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-api-metal','portable-metal-pipeline-lock','portable-numeric-metal','portable-probe-metal','portable-catalog-readiness','portable-duration-extend-unit-tests','portable-duration-extend-native-runtime-tests','portable-duration-extend-metal','portable-removal-queue-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-duration-extend-existing-parity','portable-generated-v44-comparison','portable-generated-v45-comparison','portable-duration-extend-global-gates','portable-duration-extend-transfer-completed','portable-duration-extend-optimized-transfer-completed','portable-duration-extend-timing-order','portable-enemy-fanout-parity','portable-enemy-fanout-benchmark','portable-duration-extend-baseline-validation','portable-duration-extend-work-in-progress','portable-combat-checkpoint']
for n in reports:
 d=load(n)
 if n!='portable-catalog-readiness':assert d['passed'] if 'passed' in d else d.get('metal_verified'),n
save('portable-duration-extend-validation',dict(passed=True,full_goal_complete=False,full_character_verified=0,source_commit=SOURCE,pre_optimization_source_commit=BASE,windows_gpu_runs_this_stage=2,windows_elapsed_seconds=[baseline['execution']['elapsed_seconds'],w['execution']['elapsed_seconds']],positive_cases=1131,rejections=206,native_duration_cases=39,real_profiles=58,unit_tests=127,native_runtime_tests=15,unchanged_prior_queries=len(a),unchanged_prior_full_states=len(same),unchanged_real_profiles=58,lifecycle_missing=81,efficiency_measurement_completed=True,single_receiver_ratio=bench['workloads']['one-receiver']['single_to_queued_ratio'],peak_gpu_memory_measured=False,scope='Common duration extension, independent enemy lifetimes/generation, guarded one-receiver scheduling; full catalog and all variants remain uncertified',artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},tool_sha256={str(p.relative_to(R)):sha(p) for p in [P/'benchmark-enemy-fanout.py',P/'verify-duration-extend.py',P/'build-duration-extend-cases.py']}))
print('Sealed named duration extension and optimized enemy scheduling:',len(reports),'artifacts; full goal incomplete')
