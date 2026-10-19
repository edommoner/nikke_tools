"""Audit full common protection proofs without declaring full-catalog support."""
import argparse,copy,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path.insert(0,str(P))
from protection_source_equivalence import equivalence
s=importlib.util.spec_from_file_location('normalize_generated',P/'seal-stack-increment.py');helper=importlib.util.module_from_spec(s);s.loader.exec_module(helper)
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def historical(n):return json.loads(subprocess.check_output(['git','show','e96a546:research/'+n+'.json'],cwd=R))
def main():
 m=load('portable-combat-metal');w=load(args.windows_report);g=load('portable-protection-global-gates');t=load('portable-protection-transfer-completed')
 assert m['passed'] and len(m['cases'])==1433 and len(m['rejected_cases'])==276
 assert len(m['protection_cpu_regressions'])==57 and len(m['status_cpu_regressions'])==79 and len(m['stack_cpu_regressions'])==148
 assert g['passed'] and g['complete'] and len(g['gates'])==24
 assert t['passed'] and t['remote_turn_status']=='completed' and t['windows_execution_terminal'] and t['remaining_verification_processes']==0 and t['parts']==t['total_parts']
 commit=subprocess.check_output(['git','rev-parse',args.source],cwd=R,text=True).strip();e=w['execution']
 subprocess.run(['git','diff','--exit-code',commit,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 assert w['passed'] and w['gpu_execution_verified'] and w['current_full_cuda_batch_executed'] is True
 source_equivalence=equivalence(e['commit'],commit)
 assert e['exit_code']==0 and not e['timed_out'] and e['below_normal_priority'] and e['timeout_seconds']==120
 assert w['postcheck']['remaining_verification_processes']==0 and w['postcheck']['existing_gpu_service_preserved']
 for key in ('head','status'):assert w['postcheck']['original_'+key+'_after']==e['original_'+key+'_before']
 keys=['source_sha256','validation_sha256','input_sha256','output_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
 for k in keys:assert m[k]==w[k],k
 assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
 for category in ('source_sha256','validation_sha256'):
  for path,h in m[category].items():assert sha(R/path)==h,path
 for path,h in m['source_sha256'].items():assert hashlib.sha256(subprocess.check_output(['git','show',commit+':'+path],cwd=R)).hexdigest()==h,path
 generated={}
 for backend,suffix in (('cuda','cu'),('metal','metal')):
  path=P/'portable-build'/('event_runtime.'+suffix);assert sha(path)==m['generated_sha256'][backend]
  generated[backend]=helper.normalized(path.read_bytes());assert generated[backend]==w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
 save('portable-protection-generated-comparison',dict(passed=True,source_commit=commit,windows_report=args.windows_report+'.json',source_equivalence=source_equivalence,compared_keys=keys,normalized_sha256=generated))
 p=load('portable-protection-existing-metal-parity');q=w['protection_existing_parity'];assert p['passed'] and q['passed'] and p['prior_inputs']==1625
 for k in ('source_sha256','input_sha256','output_sha256','prior_input_sha256','prior_output_sha256','prior_inputs','current_inputs','all_old_output_words_equal','all_added_old_output_tail_words_zero'):assert p[k]==q[k],k
 assert p['all_old_output_words_equal'] and p['all_added_old_output_tail_words_zero']
 save('portable-protection-existing-cuda-parity',q)
 old=historical('portable-combat-metal');assert m['results'][:len(old['results'])]==old['results']
 for k in [k for k in old if k.endswith('_cpu_regressions')]+['known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']:assert m[k]==old[k],k
 prior=historical('portable-roster-battles-metal');roster=load('portable-roster-battles-metal');strip=lambda c:{k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'}
 assert roster['passed'] and len(roster['cases'])==74
 current={(c['character'],c['grown']):strip(c) for c in roster['cases']}
 for c in prior['cases']:assert current[c['character'],c['grown']]==strip(c),(c['character'],c['grown'])
 before=load('portable-protection-before-efficiency-roster');assert before['passed'] and len(before['cases'])==74
 for c in before['cases']:
  data=current[c['character'],c['grown']];assert hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()==c['sha256']
 save('portable-protection-roster-parity',dict(passed=True,current_profiles=74,old_profiles_preserved=len(prior['cases']),before_efficiency_profiles_preserved=74,all_other_decoded_fields_and_cpu_reference_preserved=True,excluded_fields=['cpu_reference_wall_seconds']))
 units={}
 for name,count in {'unit':155,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
  row=next(r for r in g['gates'] if r['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');units[name]=dict(tests=count,output=text)
 save('portable-protection-unit-tests',dict(passed=True,groups=units))
 native=load('portable-protection-native');assert native['passed'] and len(native['cases'])==57
 for path,h in native['validation_sha256'].items():assert sha(R/path)==h,path
 api=load('portable-api-metal');assert api['passed'] and len(api['protection_execution'])==5
 audit=load('portable-catalog-readiness');assert audit['catalog_characters']==203 and audit['own_effect_preflight_passed']==37 and audit['full_character_verified']==0
 assert load('portable-protection-storage')['passed']
 if args.pre_optimization:
  save('portable-protection-pre-optimization',dict(passed=True,source_commit=commit,positive_cases=1433,rejections=276,batched_inputs=1709,native_protection_cases=57,unit_tests=155,mac_gates=24,roster_profiles=74,windows_report=args.windows_report+'.json',current_full_cuda_batch_executed=True,source_sha256=m['source_sha256'],validation_sha256=m['validation_sha256'],input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],generated_normalized_sha256=generated))
  print('Complete pre-optimization protection proofs verified');return
 efficiency=load('portable-protection-efficiency-decision');assert efficiency['passed'] and load('portable-protection-final-processes')['passed']
 if efficiency['production_change_adopted']:
  assert g['source_provenance']['source_commit']==commit and all(row['source_commit']==commit for row in g['gates'])
  assert t['windows_report']==args.windows_report+'.json'
  pre=load('portable-protection-pre-optimization');assert pre['passed'] and pre['output_sha256']==m['output_sha256']
  candidate=load('portable-protection-candidate-parity');assert candidate['passed'] and candidate['all_output_bytes_equal'] and candidate['inputs']==1709
  for path,h in candidate['parity']['mask']['source_sha256'].items():
   prefix='research/portable-build/protection-mask-mask/'
   if path.startswith(prefix+'gpu/'):assert m['source_sha256'][path[len(prefix):]]==h,path
 save('portable-combat-cuda',dict(w,summary_only=True,summary_source=args.windows_report+'.json',scope=m['scope']))
 previous=historical('portable-combat-checkpoint');save('portable-combat-v56-checkpoint',previous);cp=copy.deepcopy(previous)
 cp.update(wire_abi='0x50455665',verified_commit=commit,previous_checkpoint=dict(report='portable-combat-v56-checkpoint.json',proof_commit='e96a546'),positive_cases=1433,rejections=276,batched_inputs=1709,input_words=81920,output_words=135168,unit_tests=155,own_effect_preflight_passed=37,real_roster_profiles=74,batch_layout=m['batch_layout'],normal_ui_connected=False,normal_ui_backend='cpu',full_character_verified=0,all_characters_supported=False,full_goal_complete=False,windows_report=args.windows_report+'.json',windows_execution=e,windows_postcheck=w['postcheck'],windows_checks_this_stage=2 if efficiency['production_change_adopted'] else 1,current_full_cuda_batch_executed=True,source_provenance=dict(fixed_shared_source_commit=commit,metal_core_source_commit=e['commit'],windows_source_commit=e['commit'],source_equivalence=source_equivalence),validation_receipt='portable-protection-validation.json',generated_source_comparison='portable-protection-generated-comparison.json',existing_parity='portable-protection-existing-metal-parity.json',cuda_verification_mode='full_current_batch',cuda_comparison={k:True for k in keys},regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')},missing_families=audit['missing_families'],protection=dict(native_cases=57,api_cases=5,shield=True,decoy=True,next_shield_amp=True,shield_invincible=True,healing=True,cover_disabled=True,carrier_identity_retained_for_callbacks=True,added_private_arrays=0,added_runtime_scalars=0,added_frame_fields=0,efficiency=efficiency),next_work=['Connect remaining enemy world scheduling, modifiers, controls and effects, then certify all203 characters and variants'])
 for k in ('source_sha256','validation_sha256','input_sha256','output_sha256'):cp[k]=m[k]
 save('portable-combat-checkpoint',cp)
 reports=['portable-combat-v56-checkpoint','portable-combat-metal','portable-combat-cuda','portable-combat-checkpoint',args.windows_report,'portable-protection-generated-comparison','portable-protection-existing-metal-parity','portable-protection-existing-cuda-parity','portable-protection-global-gates','portable-protection-transfer-completed','portable-protection-unit-tests','portable-protection-native','portable-protection-metal','portable-protection-storage','portable-protection-roster-parity','portable-protection-timing-order','portable-protection-pre-optimization','portable-protection-candidate-parity','portable-protection-benchmark','portable-protection-efficiency-decision','portable-protection-final-processes','portable-protection-api-sentinel-fix','portable-roster-battles-metal','portable-api-metal','portable-catalog-readiness','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock','portable-duration-extend-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-queue-metal','portable-stack-numeric-metal','portable-stack-notices-metal']
 reports += [p.stem for p in P.glob('portable-protection-*-failure.json')]
 if efficiency['production_change_adopted']:reports += ['windows-portable-combat-v57','portable-protection-initial-global-gates','portable-protection-initial-transfer-completed','portable-protection-before-efficiency-metal','portable-protection-before-efficiency-roster','portable-protection-initial-generated-comparison','portable-protection-unversioned-benchmark','portable-protection-unversioned-candidate-parity']
 tools=[P/n for n in ('build-protection-cases.py','verify-protection.py','verify-protection-regression.py','run-protection-gates.py','verify-protection-storage.py','protection-terminal-check.py','benchmark-protection.py','protection_source_equivalence.py','seal-protection.py')]
 save('portable-protection-validation',dict(passed=True,source_commit=commit,positive_cases=1433,rejections=276,batched_inputs=1709,unit_tests=155,native_protection_cases=57,real_profiles=74,current_full_cuda_batch_executed=True,normal_ui_backend='cpu',full_goal_complete=False,full_character_verified=0,artifact_scope=dict(current_gpu='Common full-core reports',component_gpu='portable-protection-metal is the earlier57-program development dispatch; current57 native checks are in the full core report',diagnostics='*-failure.json retain repaired development findings',world='Authored target/cover masks enter the shared landing boundary; automatic boss-world scheduling remains unported'),documentation_sha256={str(p.relative_to(R)):sha(p) for p in [R/'docs'/n for n in ('portable-protection.md','mac-handoff.md','mac-migration.md','portable-combat-runtime.md')]},artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},tool_sha256={str(p.relative_to(R)):sha(p) for p in tools}))
 print('Protection proofs sealed; full catalog goal remains incomplete.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',default='c411ddc');p.add_argument('--windows-report',default='windows-portable-combat-v58');p.add_argument('--pre-optimization',action='store_true');args=p.parse_args();main()
