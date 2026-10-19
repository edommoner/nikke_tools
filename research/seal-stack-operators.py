"""Seal v51 component evidence without certifying the unfinished full catalog."""
import copy,hashlib,importlib.util,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='ba890da'
spec=importlib.util.spec_from_file_location('previous_sealer',P/'seal-stack-increment.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def historical(n):return json.loads(subprocess.check_output(['git','show','029aa07:research/'+n+'.json'],cwd=R))
def main():
 m=load('portable-combat-metal');w=load('windows-portable-combat-v52');g=load('portable-stack-operators-global-gates');t=load('portable-stack-operators-transfer-completed')
 assert m['passed'] and len(m['cases'])==1297 and len(m['rejected_cases'])==231
 assert len(m['stack_cpu_regressions'])==148 and len(m['mode_session_cpu_regressions'])==41
 assert m['known_mode_cpu_differences']==[]
 for k in ('known_cpu_differences','known_health_cpu_differences'):assert m[k]==historical('portable-combat-metal')[k]
 assert g['passed'] and g['complete'] and len(g['gates'])==22
 assert t['passed'] and t['remote_turn_status']=='completed' and t['parts']==t['total_parts']
 commit=subprocess.check_output(['git','rev-parse',SOURCE],cwd=R,text=True).strip()
 assert w['passed'] and w['gpu_execution_verified'] and w['execution']['commit']==commit
 e=w['execution'];assert e['exit_code']==0 and not e['timed_out'] and e['below_normal_priority'] and e['timeout_seconds']==120
 assert w['postcheck']['remaining_verification_processes']==0 and w['postcheck']['existing_gpu_service_preserved']
 for k in ('head','status'):assert w['postcheck']['original_'+k+'_after']==e['original_'+k+'_before']
 keys=['source_sha256','input_sha256','output_sha256','validation_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
 for k in keys:assert m[k]==w[k],k
 assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
 for k in ('source_sha256','validation_sha256'):
  for p,h in m[k].items():assert sha(R/p)==h,p
 generated={}
 for backend,suffix in [('cuda','cu'),('metal','metal')]:
  p=P/'portable-build'/('event_runtime.'+suffix);assert sha(p)==m['generated_sha256'][backend]
  generated[backend]=old.normalized(p.read_bytes());assert generated[backend]==w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
 save('portable-generated-v52-comparison',dict(passed=True,source_commit=commit,compared_keys=keys,normalized_sha256=generated))
 parity=load('portable-stack-existing-metal-parity');remote=w['stack_existing_parity'];assert parity['passed'] and remote['passed']
 for k in ('source_sha256','input_sha256','output_sha256','current_subset_input_sha256','current_subset_output_sha256','prior_input_sha256','prior_output_sha256','prior_inputs','current_inputs'):assert parity[k]==remote[k],k
 save('portable-stack-existing-cuda-parity',remote)
 contract=load('portable-stack-previous-output-contract');assert contract['all_non_activation_timestamp_words_equal'] and len(contract['changed_cases'])==18
 native=load('portable-stack-prior-native-timestamps');assert native['passed'] and len(native['cases'])==18
 assert all(c['passed'] for c in native['cases'])
 for k in ('source_sha256','input_sha256','output_sha256'):assert parity[k]==m[k],k
 roster=load('portable-roster-battles-metal');prior=historical('portable-roster-battles-metal');strip=lambda c:{k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'}
 assert roster['passed'] and len(roster['cases'])==60
 current={(c['character'],c['grown']):strip(c) for c in roster['cases']}
 for c in prior['cases']:assert current[c['character'],c['grown']]==strip(c),(c['character'],c['grown'])
 unit={}
 for name,count in {'unit':138,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
  row=next(r for r in g['gates'] if r['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');unit[name]=dict(tests=count,output=text)
 save('portable-stack-operators-unit-tests',dict(passed=True,groups=unit))
 efficiency=load('portable-stack-operators-efficiency-decision');assert efficiency['passed'] and not efficiency['production_change_adopted']
 for n in ('portable-stack-operators-benchmark','portable-stack-operators-v2-benchmark'):
  b=load(n);assert b['passed'] and b['all_positive_and_negative_output_words_equal'] and b['inputs']==1528
 audit=load('portable-catalog-readiness');assert audit['catalog_characters']==203 and audit['own_effect_preflight_passed']==30 and audit['full_character_verified']==0
 save('portable-combat-cuda',dict(w,summary_only=True,summary_source='windows-portable-combat-v52.json',scope=m['scope']))
 prior_cp=historical('portable-combat-checkpoint');save('portable-combat-v50-checkpoint',prior_cp)
 cp=copy.deepcopy(prior_cp);cp.update(positive_cases=1297,rejections=231,batched_inputs=1528,unit_tests=138,real_roster_profiles=60,own_effect_preflight_passed=30,enemy_resident_per_recipient=False,enemy_resident_policy='Normal enemy activation fans out; stack initialization retains one shared carrier with frozen target generations.',wire_abi='0x50455662',input_words=77824,output_words=94208,batch_layout=m['batch_layout'],verified_commit=commit,source_provenance=dict(fixed_shared_source_commit=commit,metal_core_report_source_commit=commit,windows_source_commit=commit),previous_checkpoint=dict(report='portable-combat-v50-checkpoint.json',proof_commit='029aa07'),windows_report='windows-portable-combat-v52.json',windows_checks_this_stage=2,windows_execution=e,windows_postcheck=w['postcheck'],validation_receipt='portable-stack-operators-validation.json',generated_source_comparison='portable-generated-v52-comparison.json',existing_parity='portable-stack-existing-metal-parity.json',stack_operators=dict(efficiency_evaluated=True,efficiency_adopted=False,efficiency_decision='portable-stack-operators-efficiency-decision.json',new_effect_kinds_admitted=True,kinds=[16,17,18,19,20,21],immunity=True,native_cases=148,old_timestamp_corrections=18,added_private_arrays=0,added_runtime_scalars=0,added_frame_fields=0),normal_ui_backend='cpu',normal_ui_connected=False,full_goal_complete=False,full_character_verified=0,all_characters_supported=False,next_work=['Complete remaining lifecycle/world/control/effect families and certify all variants'])
 for k in ('source_sha256','input_sha256','output_sha256','validation_sha256'):cp[k]=m[k]
 save('portable-combat-checkpoint',cp)
 reports=['portable-combat-metal','portable-combat-cuda','windows-portable-combat-v52','windows-portable-combat-v51','portable-stack-operators-initial-transfer-completed','portable-stack-operators-initial-gates','portable-generated-v52-comparison','portable-stack-existing-metal-parity','portable-stack-existing-cuda-parity','portable-stack-previous-output-contract','portable-stack-prior-native-timestamps','portable-stack-operators-global-gates','portable-stack-operators-transfer-completed','portable-stack-operators-unit-tests','portable-stack-operators-timing-order','portable-stack-operators-benchmark','portable-stack-operators-candidate-parity','portable-stack-operators-benchmark-stimulus-repair','portable-stack-operators-v2-benchmark','portable-stack-operators-v2-candidate-parity','portable-stack-operators-efficiency-decision','portable-stack-operators-metal','portable-stack-operators-storage','portable-stack-operators-terminal','portable-stack-operator-admission-repair','portable-stack-operators-v51-initial-comparison','portable-combat-checkpoint','portable-roster-battles-metal','portable-api-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock','portable-duration-extend-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-queue-metal','portable-catalog-readiness','portable-stack-numeric-metal','portable-stack-notices-metal']
 reports += [p.stem for p in P.glob('portable-stack-*-failure.json') if p.stem not in reports]
 tools=[P/n for n in ('verify-stack-regression.py','verify-stack-operators.py','verify-stack-prior-timestamps.py','build-stack-cases.py','stack_case_extensions.py','stack_case_physical.py','run-stack-operator-gates.py','seal-stack-operators.py','benchmark-stack-operators.py','benchmark-stack-operators-v2.py')]
 save('portable-stack-operators-validation',dict(passed=True,source_commit=commit,positive_cases=1297,rejections=231,native_stack_cases=148,native_mode_cases=41,unit_tests=138,real_profiles=60,full_goal_complete=False,full_character_verified=0,windows_runs_this_source=1,windows_runs_this_stage=2,artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},tool_sha256={str(p.relative_to(R)):sha(p) for p in tools}))
 print('Stack operators sealed; all-character goal remains incomplete.')
if __name__=='__main__':main()
