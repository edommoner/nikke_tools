"""Verify and seal shared status evidence while retaining the unfinished full goal."""
import copy,hashlib,importlib.util,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='d2ba01a'
s=importlib.util.spec_from_file_location('previous_sealer',P/'seal-stack-increment.py');previous=importlib.util.module_from_spec(s);s.loader.exec_module(previous)
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def historical(n):return json.loads(subprocess.check_output(['git','show','3f661c8:research/'+n+'.json'],cwd=R))
def main():
 m=load('portable-combat-metal');w=load('windows-portable-combat-v56');g=load('portable-status-global-gates');t=load('portable-status-transfer-completed')
 assert m['passed'] and len(m['cases'])==1376 and len(m['rejected_cases'])==249
 assert len(m['status_cpu_regressions'])==79 and len(m['stack_cpu_regressions'])==148
 assert g['passed'] and g['complete'] and len(g['gates'])==23
 assert t['passed'] and t['remote_turn_status']=='completed' and t['parts']==t['total_parts']
 for n in ('portable-status-initial-transfer-completed','portable-status-snapshot-transfer-completed','portable-status-marker-transfer-completed'):
  transfer=load(n);assert transfer['passed'] and transfer['remote_turn_status']=='completed' and transfer['parts']==transfer['total_parts']
 commit=subprocess.check_output(['git','rev-parse',SOURCE],cwd=R,text=True).strip();e=w['execution']
 assert w['passed'] and w['gpu_execution_verified'] and e['commit']==commit and w['current_full_cuda_batch_executed'] is True
 assert e['exit_code']==0 and not e['timed_out'] and e['below_normal_priority'] and e['timeout_seconds']==120
 assert w['postcheck']['remaining_verification_processes']==0 and w['postcheck']['existing_gpu_service_preserved']
 for k in ('head','status'):assert w['postcheck']['original_'+k+'_after']==e['original_'+k+'_before']
 keys=['source_sha256','validation_sha256','input_sha256','output_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
 for k in keys:assert m[k]==w[k],k
 assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
 for k in ('source_sha256','validation_sha256'):
  for path,h in m[k].items():assert sha(R/path)==h,path
 generated={}
 for backend,suffix in [('cuda','cu'),('metal','metal')]:
  path=P/'portable-build'/('event_runtime.'+suffix);assert sha(path)==m['generated_sha256'][backend]
  generated[backend]=previous.normalized(path.read_bytes());assert generated[backend]==w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
 save('portable-generated-v56-comparison',dict(passed=True,source_commit=commit,compared_keys=keys,normalized_sha256=generated))
 p=load('portable-status-existing-metal-parity');q=w['status_existing_parity']
 assert p['passed'] and q['passed'] and p['prior_inputs']==1528 and p['all_added_tail_words_zero']
 for k in ('source_sha256','input_sha256','output_sha256','current_subset_input_sha256','current_subset_output_sha256','prior_input_sha256','prior_output_sha256','prior_inputs','current_inputs'):assert p[k]==q[k],k
 save('portable-status-existing-cuda-parity',q)
 contract=load('portable-status-previous-output-contract');assert len(contract['changed_cases'])==1
 changed=contract['changed_cases'][0];assert changed['name']=='lazy-cache-capacity' and changed['old_status']==64 and changed['new_status']==0
 repair=load('portable-status-lazy-capacity-repair');assert repair['passed'] and repair['old_input_native_valid'] and repair['statuses']==[0,64]
 old=historical('portable-combat-metal');assert m['results'][:len(old['results'])]==old['results']
 for k in ('known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences'):assert m[k]==old[k]
 roster=load('portable-roster-battles-metal');prior=historical('portable-roster-battles-metal');strip=lambda c:{k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'}
 assert roster['passed'] and len(roster['cases'])==64;current={(c['character'],c['grown']):strip(c) for c in roster['cases']}
 for c in prior['cases']:assert current[c['character'],c['grown']]==strip(c),(c['character'],c['grown'])
 unit={}
 for name,count in {'unit':146,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
  row=next(r for r in g['gates'] if r['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');unit[name]=dict(tests=count,output=text)
 save('portable-status-unit-tests',dict(passed=True,groups=unit))
 native=load('portable-status-native-contract');assert native['passed'] and len(native['cases'])==79
 api=load('portable-api-metal');assert api['passed'] and len(api['status_execution'])==5
 audit=load('portable-catalog-readiness');assert audit['catalog_characters']==203 and audit['own_effect_preflight_passed']==32 and audit['full_character_verified']==0
 efficiency=load('portable-status-efficiency-decision');assert efficiency['passed'] and efficiency['production_change_adopted']
 candidate=load('portable-status-candidate-parity');assert candidate['passed'] and candidate['inputs']==1625 and candidate['all_output_bytes_equal']
 for path,h in candidate['parity']['touched']['source_sha256'].items():
  prefix='research/portable-build/status-clear-touched/'
  if path.startswith(prefix+'gpu/'):assert m['source_sha256'][path[len(prefix):]]==h,path
 pre=load('portable-status-pre-optimization');assert pre['passed'] and pre['mac_gates']==23 and pre['current_full_cuda_batch_executed'] is False
 for k in ('input_sha256','output_sha256','validation_sha256'):assert pre[k]==m[k],k
 assert [k for k,v in m['source_sha256'].items() if pre['source_sha256'].get(k)!=v]==['gpu/status_runtime.slang']
 boundary=load('portable-status-clear-boundaries-metal');other=w['status_clear_boundaries'];assert boundary['passed'] and other['passed'] and len(boundary['cases'])==2
 for k in ('cases','source_sha256','validation_sha256','input_sha256','output_sha256','actual_statuses','expected_statuses'):assert boundary[k]==other[k],k
 assert boundary['source_sha256']==m['source_sha256']
 for path,h in boundary['validation_sha256'].items():assert sha(R/path)==h,path
 save('portable-status-clear-boundaries-cuda',other)
 assert load('portable-status-storage')['passed'] and load('portable-status-roster-parity')['passed'] and load('portable-status-final-processes')['passed']

 save('portable-combat-cuda',dict(w,summary_only=True,summary_source='windows-portable-combat-v56.json',scope=m['scope']))
 prior_cp=historical('portable-combat-checkpoint');save('portable-combat-v52-checkpoint',prior_cp)
 cp=copy.deepcopy(prior_cp);cp.update(positive_cases=1376,rejections=249,batched_inputs=1625,unit_tests=146,real_roster_profiles=64,own_effect_preflight_passed=32,wire_abi='0x50455663',input_words=77824,output_words=102400,batch_layout=m['batch_layout'],verified_commit=commit,source_provenance=dict(fixed_shared_source_commit=commit,metal_core_report_source_commit=commit,windows_source_commit=commit),previous_checkpoint=dict(report='portable-combat-v52-checkpoint.json',proof_commit='3f661c8'),windows_report='windows-portable-combat-v56.json',windows_checks_this_stage=4,current_full_cuda_batch_executed=True,cuda_verification_mode='full_current_batch',windows_execution=e,windows_postcheck=w['postcheck'],validation_receipt='portable-status-validation.json',generated_source_comparison='portable-generated-v56-comparison.json',existing_parity='portable-status-existing-metal-parity.json',status=dict(cleanse=True,immunity=['unlimited','named','counted'],native_cases=79,former_capacity_rejection_now_native_positive=True,output_growth_bytes=32768,added_private_arrays=0,added_runtime_scalars=0,added_frame_fields=0,efficiency=efficiency),normal_ui_backend='cpu',normal_ui_connected=False,full_goal_complete=False,full_character_verified=0,all_characters_supported=False,next_work=['Complete remaining lifecycle/world/protection/control/effect families and certify all variants'])
 cp.pop('gpu_dispatches',None)
 cp.update(core_gpu_dispatches=1,additional_boundary_dispatches=1,missing_families=audit['missing_families'],status_api_cases=5,status_clear_boundary_cases=2,regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')},cuda_comparison={k:True for k in keys},historical_windows_reports=['windows-portable-combat-v53.json','windows-portable-combat-v54.json','windows-portable-combat-v55.json'],status_preoptimization_proof='portable-status-pre-optimization.json')
 for k in ('source_sha256','validation_sha256','input_sha256','output_sha256'):cp[k]=m[k]
 save('portable-combat-checkpoint',cp)
 reports=['portable-combat-metal','portable-combat-cuda','windows-portable-combat-v56','portable-generated-v56-comparison','portable-status-existing-metal-parity','portable-status-existing-cuda-parity','portable-status-previous-output-contract','portable-status-lazy-capacity-repair','portable-status-global-gates','portable-status-transfer-completed','portable-status-unit-tests','portable-status-native-contract','portable-status-operators-metal','portable-status-storage','portable-status-timing-order','portable-status-benchmark','portable-status-efficiency-decision','portable-combat-checkpoint','portable-roster-battles-metal','portable-api-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock','portable-duration-extend-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-queue-metal','portable-catalog-readiness','portable-stack-numeric-metal','portable-stack-notices-metal']
 reports += ['windows-portable-combat-v53','windows-portable-combat-v54','windows-portable-combat-v55','portable-generated-v55-comparison','portable-status-pre-optimization','portable-status-candidate-parity','portable-status-before-efficiency-metal','portable-status-before-efficiency-global-gates','portable-status-initial-gates','portable-status-initial-transfer-completed','portable-status-snapshot-transfer-completed','portable-status-marker-transfer-completed','portable-status-snapshot-incremental','portable-status-marker-incremental','portable-status-before-marker-metal','portable-status-before-marker-roster','portable-status-snapshot-global-gates','portable-status-snapshot-metal','portable-status-marker-metal','portable-status-clear-boundaries-metal','portable-status-clear-boundaries-cuda','portable-status-final-processes','portable-status-roster-parity']
 reports += [p.stem for p in P.glob('portable-status-*-failure.json') if p.stem not in reports]
 tools=[P/n for n in ('build-status-cases.py','status_case_extensions.py','verify-status-native-contract.py','verify-status-operators.py','verify-status-lazy-capacity.py','verify-status-regression.py','verify-status-snapshot-parity.py','verify-status-snapshot-delta.py','verify-status-marker-parity.py','verify-status-marker-delta.py','verify-status-clear-boundaries.py','verify-status-final.py','verify-status-storage.py','verify-status-roster-parity.py','status-terminal-check.py','run-status-gates.py','benchmark-status.py','seal-status-incremental.py','seal-status.py')]
 save('portable-status-validation',dict(passed=True,source_commit=commit,positive_cases=1376,rejections=249,native_status_cases=79,unit_tests=146,real_profiles=64,windows_runs_this_source=1,windows_runs_this_stage=4,current_full_cuda_batch_executed=True,artifact_scope=dict(current_core='portable-combat-metal.json and windows-portable-combat-v56.json',current_boundary='portable-status-clear-boundaries-metal.json and cuda counterpart',preoptimization='v53/v54/v55, incremental proofs and before-efficiency reports',development_history='portable-status-operators-metal.json was dispatched before optimization; current79 CPU/GPU checks are in the full core report',diagnostics='*-failure.json preserve repaired development failures; they are not final gates'),full_goal_complete=False,full_character_verified=0,artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},tool_sha256={str(p.relative_to(R)):sha(p) for p in tools}))
 print('Shared status evidence sealed; full catalog goal remains incomplete.')
if __name__=='__main__':main()
