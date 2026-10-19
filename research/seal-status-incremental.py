"""Historical8c1735b sealer; requires matching pre-optimization source/reports.
Use seal-status.py for the final optimized source.
"""
import argparse,copy,hashlib,importlib.util,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='8c1735b'
s=importlib.util.spec_from_file_location('old_sealer',P/'seal-stack-increment.py');old_sealer=importlib.util.module_from_spec(s);s.loader.exec_module(old_sealer)
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def historical(n):return json.loads(subprocess.check_output(['git','show','3f661c8:research/'+n+'.json'],cwd=R))
def main():
 m=load('portable-combat-metal');baseline=load('windows-portable-combat-v53');snapshot=load('windows-portable-combat-v54');delta=load('windows-portable-combat-v55');inc1=load('portable-status-snapshot-incremental');inc2=load('portable-status-marker-incremental');parent=load('portable-status-before-marker-metal');g=load('portable-status-global-gates')
 assert m['passed'] and len(m['cases'])==1376 and len(m['rejected_cases'])==249 and len(m['status_cpu_regressions'])==79 and len(m['stack_cpu_regressions'])==148
 assert g['passed'] and g['complete'] and len(g['gates'])==23
 commit=subprocess.check_output(['git','rev-parse',SOURCE],cwd=R,text=True).strip()
 expected_commits=[inc1['baseline_source_commit'],subprocess.check_output(['git','rev-parse','1662c46'],cwd=R,text=True).strip(),commit]
 for w,expected in zip((baseline,snapshot,delta),expected_commits):
  e=w['execution'];assert w['passed'] and w['gpu_execution_verified'] and e['commit']==expected
  assert e['exit_code']==0 and not e['timed_out'] and e['below_normal_priority'] and e['timeout_seconds']==120
  assert w['postcheck']['remaining_verification_processes']==0 and w['postcheck']['existing_gpu_service_preserved']
  for k in ('head','status'):assert w['postcheck']['original_'+k+'_after']==e['original_'+k+'_before']
 for name in ('portable-status-initial-transfer-completed','portable-status-snapshot-transfer-completed','portable-status-transfer-completed'):
  t=load(name);assert t['passed'] and t['remote_turn_status']=='completed' and t['parts']==t['total_parts']
 assert inc1['old_cases_affected_by_new_snapshot_observer_predicate']==[]
 actual=baseline['actual_statuses'];prior=baseline
 for proof,w,full in ((inc1,snapshot,parent),(inc2,delta,m)):
  assert proof['passed'] and proof['gpu_source_unchanged'] and proof['no_input_or_output_word_normalization'] and proof['entry_thread_index_used_only_for_guard_and_wire_offsets']
  assert len(actual)==proof['old_inputs']
  for k in ('input_sha256','output_sha256'):
   assert proof['old_subset_'+k]==prior[k]
   assert proof['delta_'+k]==w[k]
   assert proof['current_full_execution'][k]==full[k]
  assert w['current_full_cuda_batch_executed'] is False and w['unit_tests']['passed'] and w['unit_tests']['count']==8
  assert [c['name'] for c in w['cases']]==proof['delta_cases']
  values=[None]*proof['current_inputs'];mapping=proof['subset_mapping'];extra=proof['delta_indices']
  assert len(set(mapping+extra))==len(values)
  for at,value in zip(mapping,actual):values[at]=value
  for at,value in zip(extra,w['actual_statuses']):values[at]=value
  actual=values;prior=full
 assert actual==m['actual_statuses']==m['expected_statuses'] and len(actual)==1625
 assert baseline['rejected_cases']==m['rejected_cases']
 assert m['source_sha256']==baseline['source_sha256']==snapshot['source_sha256']==delta['source_sha256']==inc1['source_sha256']==inc2['source_sha256']
 for kind in ('source_sha256','validation_sha256'):
  for path,h in m[kind].items():assert sha(R/path)==h,path
 for path,h in delta['validation_sha256'].items():assert sha(R/path)==h,path
 assert set(inc1['changed_validation_paths'])=={'app/reference_health_runtime.py','tests/fixtures/portable-status.json'}
 assert set(inc2['changed_validation_paths'])=={'app/portable_runtime.py','tests/fixtures/portable-status.json'}
 changed=[k for k,v in m['validation_sha256'].items() if baseline['validation_sha256'].get(k)!=v]
 assert set(changed)=={'app/reference_health_runtime.py','app/portable_runtime.py','tests/fixtures/portable-status.json'}
 new_names=inc1['delta_cases']+inc2['delta_cases']
 assert baseline['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases'] if c['name'] not in new_names]
 for key in [k for k in m if k.endswith('_cpu_regressions')]+['known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']:
  projected=[n for n in m[key] if n not in new_names] if key=='status_cpu_regressions' else m[key]
  assert projected==baseline[key],key
 generated={}
 for backend,suffix in (('cuda','cu'),('metal','metal')):
  path=P/'portable-build'/('event_runtime.'+suffix);assert sha(path)==m['generated_sha256'][backend]
  generated[backend]=old_sealer.normalized(path.read_bytes())
  for w in (baseline,snapshot,delta):assert generated[backend]==w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
 save('portable-generated-v55-comparison',dict(passed=True,source_commit=commit,gpu_source_unchanged=True,normalized_sha256=generated,current_full_cuda_batch_executed=False,verification_mode='Unchanged 1622-program CUDA baseline plus two snapshot programs and one nullable-marker program; exact input/full-output subset proofs, no word normalization.'))
 old=historical('portable-combat-metal');assert m['results'][:len(old['results'])]==old['results']
 contract=load('portable-status-previous-output-contract');assert len(contract['changed_cases'])==1 and contract['all_added_tail_words_zero']
 c=contract['changed_cases'][0];assert c['name']=='lazy-cache-capacity' and c['old_status']==64 and c['new_status']==0
 repair=load('portable-status-lazy-capacity-repair');assert repair['passed'] and repair['old_input_native_valid'] and repair['statuses']==[0,64]
 parity=load('portable-status-existing-metal-parity');assert parity['passed']
 for k in ('input_sha256','output_sha256','source_sha256'):assert parity[k]==m[k]
 roster=load('portable-roster-battles-metal');prior=historical('portable-roster-battles-metal');strip=lambda c:{k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'}
 assert roster['passed'] and len(roster['cases'])==64;current={(c['character'],c['grown']):strip(c) for c in roster['cases']}
 for c in prior['cases']:assert current[c['character'],c['grown']]==strip(c),(c['character'],c['grown'])
 units={}
 for name,count in {'unit':146,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
  row=next(r for r in g['gates'] if r['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');units[name]=dict(tests=count,output=text)
 save('portable-status-unit-tests',dict(passed=True,groups=units,windows_related_tests=delta['unit_tests']))
 assert load('portable-status-native-contract')['passed'] and len(load('portable-status-native-contract')['cases'])==79
 assert load('portable-api-metal')['passed'] and len(load('portable-api-metal')['status_execution'])==5
 audit=load('portable-catalog-readiness');assert audit['catalog_characters']==203 and audit['own_effect_preflight_passed']==32 and audit['full_character_verified']==0
 if args.verification_only:
  save('portable-status-pre-optimization',dict(passed=True,source_commit=commit,positive_cases=1376,rejections=249,native_status_cases=79,unit_tests=146,mac_gates=23,windows_reports=['windows-portable-combat-v53.json','windows-portable-combat-v54.json','windows-portable-combat-v55.json'],current_full_cuda_batch_executed=False,source_sha256=m['source_sha256'],validation_sha256=m['validation_sha256'],input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],generated_normalized_sha256=generated,actual_statuses_composed=actual))
  print('Complete pre-optimization correctness proof checked');return
 efficiency=load('portable-status-efficiency-decision');assert efficiency['passed']
 assert load('portable-status-storage')['passed'] and load('portable-status-final-processes')['passed']
 cuda=dict(passed=True,gpu_execution_verified=True,backend='cuda',summary_only=True,verification_mode='unchanged_full_baseline_plus_two_deltas',current_full_cuda_batch_executed=False,source_sha256=m['source_sha256'],validation_sha256=m['validation_sha256'],derived_current_input_sha256=m['input_sha256'],derived_current_output_sha256=m['output_sha256'],actual_statuses_composed=actual,baseline_report='windows-portable-combat-v53.json',delta_reports=['windows-portable-combat-v54.json','windows-portable-combat-v55.json'],incremental_proofs=['portable-status-snapshot-incremental.json','portable-status-marker-incremental.json'],baseline_inputs=1622,delta_inputs=[2,1],cases=[dict(name=c['name'],passed=c['passed']) for c in m['cases']],scope=m['scope'])
 save('portable-combat-cuda',cuda)
 previous=historical('portable-combat-checkpoint');save('portable-combat-v52-checkpoint',previous);cp=copy.deepcopy(previous)
 cp.update(positive_cases=1376,rejections=249,batched_inputs=1625,unit_tests=146,real_roster_profiles=64,own_effect_preflight_passed=32,wire_abi='0x50455663',input_words=77824,output_words=102400,batch_layout=m['batch_layout'],verified_commit=commit,source_provenance=dict(shared_source_commit=commit,windows_baseline_commit=baseline['execution']['commit'],windows_delta_commits=expected_commits[1:],gpu_source_unchanged_between_baseline_and_delta=True),previous_checkpoint=dict(report='portable-combat-v52-checkpoint.json',proof_commit='3f661c8'),windows_report='windows-portable-combat-v55.json',windows_baseline_report='windows-portable-combat-v53.json',windows_checks_this_stage=3,cuda_verification_mode='unchanged_full_baseline_plus_two_deltas',current_full_cuda_batch_executed=False,windows_execution=delta['execution'],windows_postcheck=delta['postcheck'],validation_receipt='portable-status-validation.json',generated_source_comparison='portable-generated-v55-comparison.json',existing_parity='portable-status-existing-metal-parity.json',status=dict(cleanse=True,immunity=['unlimited','named','counted'],native_cases=79,former_capacity_rejection_now_native_positive=True,output_growth_bytes=32768,added_private_arrays=0,added_runtime_scalars=0,added_frame_fields=0,efficiency=efficiency),normal_ui_backend='cpu',normal_ui_connected=False,full_goal_complete=False,full_character_verified=0,all_characters_supported=False,next_work=['Complete remaining lifecycle/world/protection/control/effect families and certify all variants'])
 cp.pop('gpu_dispatches',None)
 cp.update(metal_gpu_dispatches=1,cuda_proof_batches=3,status_api_cases=5,missing_families=audit['missing_families'],regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')},cuda_comparison=dict(shared_gpu_source=True,exact_input_subset_proofs=True,exact_full_output_subset_proofs=True,composed_statuses=True,cpu_observations=True,normalized_generated_source=True,current_full_cuda_batch_executed=False))
 for k in ('source_sha256','validation_sha256','input_sha256','output_sha256'):cp[k]=m[k]
 save('portable-combat-checkpoint',cp)
 reports=['portable-combat-metal','portable-combat-cuda','windows-portable-combat-v53','windows-portable-combat-v54','windows-portable-combat-v55','portable-generated-v55-comparison','portable-status-existing-metal-parity','portable-status-previous-output-contract','portable-status-lazy-capacity-repair','portable-status-snapshot-incremental','portable-status-snapshot-metal','portable-status-global-gates','portable-status-initial-gates','portable-status-initial-transfer-completed','portable-status-snapshot-transfer-completed','portable-status-transfer-completed','portable-status-unit-tests','portable-status-native-contract','portable-status-operators-metal','portable-status-storage','portable-status-timing-order','portable-status-benchmark','portable-status-candidate-parity','portable-status-efficiency-decision','portable-combat-checkpoint','portable-roster-battles-metal','portable-api-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock','portable-duration-extend-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-queue-metal','portable-catalog-readiness','portable-stack-numeric-metal','portable-stack-notices-metal']
 reports += ['portable-status-marker-incremental','portable-status-marker-metal','portable-status-before-marker-metal','portable-status-before-marker-roster','portable-status-snapshot-global-gates','portable-status-final-processes','portable-status-roster-parity']
 reports += [p.stem for p in P.glob('portable-status-*-failure.json') if p.stem not in reports]
 tools=[P/n for n in ('build-status-cases.py','status_case_extensions.py','verify-status-native-contract.py','verify-status-operators.py','verify-status-lazy-capacity.py','verify-status-regression.py','verify-status-snapshot-parity.py','verify-status-snapshot-delta.py','verify-status-marker-parity.py','verify-status-marker-delta.py','run-status-gates.py','benchmark-status.py','verify-status-storage.py','verify-status-roster-parity.py','status-terminal-check.py','seal-status.py')]
 save('portable-status-validation',dict(passed=True,source_commit=commit,positive_cases=1376,rejections=249,native_status_cases=79,unit_tests=146,real_profiles=64,windows_runs_this_stage=3,cuda_verification_mode='unchanged_full_baseline_plus_two_deltas',current_full_cuda_batch_executed=False,full_goal_complete=False,full_character_verified=0,artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},tool_sha256={str(p.relative_to(R)):sha(p) for p in tools}))
 print('Status evidence sealed; full catalog goal remains incomplete.')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--verification-only',action='store_true');args=parser.parse_args();main()
