"""Seal current split proofs without declaring full-catalog GPU certification."""
import argparse,copy,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path.insert(0,str(R/'app'))
from portable_specs import ABI,LIMITS as L
s=importlib.util.spec_from_file_location('normalizer',P/'seal-stack-increment.py');helper=importlib.util.module_from_spec(s);s.loader.exec_module(helper)
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def old(n):return json.loads(subprocess.check_output(['git','show','b8ae1c7:research/'+n+'.json'],cwd=R))
def case_sha(c):return hashlib.sha256(json.dumps({k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
 assert load('portable-instant-list-admission-probe-metal')['full_instant_list_supported'],'Resolve the ordered instant boundary before full-stage sealing'
 m=load('portable-combat-metal');w=load(args.windows_report);g=load('portable-split-global-gates');t=load('portable-split-transfer-completed')
 source=subprocess.check_output(['git','rev-parse',args.source],cwd=R,text=True).strip();subprocess.run(['git','diff','--exit-code',source,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
 assert m['passed'] and len(m['cases'])==1479 and len(m['rejected_cases'])==294 and len(m['actual_statuses'])==1773
 assert len(m['protection_cpu_regressions'])==103 and len(m['status_cpu_regressions'])==79 and len(m['stack_cpu_regressions'])==148
 assert g['passed'] and g['complete'] and len(g['gates'])==25 and g['source_commit']==source and all(r['source_commit']==source for r in g['gates'])
 assert t['passed'] and t['remote_turn_status']=='completed' and t['parts']==t['total_parts'] and t['windows_execution_terminal'] and t['windows_report']==args.windows_report+'.json'
 assert w['passed'] and w['gpu_execution_verified'] and w['current_full_cuda_batch_executed'] and w['execution']['commit']==source
 e=w['execution'];post=w['postcheck'];assert e['exit_code']==0 and not e['timed_out'] and e['below_normal_priority'] and e['timeout_seconds']==120
 assert post['remaining_verification_processes']==0 and post['existing_gpu_service_preserved']
 for k in ('head','status'):assert post['original_'+k+'_after']==e['original_'+k+'_before']
 keys=['source_sha256','validation_sha256','input_sha256','output_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
 for k in keys:assert m[k]==w[k],k
 assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
 for category in ('source_sha256','validation_sha256'):
  for p,h in m[category].items():assert digest(R/p)==h,p
 for p,h in m['source_sha256'].items():assert hashlib.sha256(subprocess.check_output(['git','show',source+':'+p],cwd=R)).hexdigest()==h,p
 normalized={}
 for backend,suffix in (('cuda','cu'),('metal','metal')):
  p=P/'portable-build'/('event_runtime.'+suffix);assert digest(p)==m['generated_sha256'][backend]
  normalized[backend]=helper.normalized(p.read_bytes());assert normalized[backend]==w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
 save('portable-split-generated-comparison',dict(passed=True,source_commit=source,windows_report=args.windows_report+'.json',compared_keys=keys,normalized_sha256=normalized))
 p=load('portable-split-existing-metal-parity');q=w['split_existing_parity'];assert p['passed'] and q['passed'] and p['prior_inputs']==1709
 for k in ('source_sha256','input_sha256','output_sha256','prior_input_sha256','prior_output_sha256','prior_inputs','current_inputs','all_old_output_words_equal','all_added_old_output_tail_words_zero'):assert p[k]==q[k],k
 save('portable-split-existing-cuda-parity',q)
 prior=old('portable-combat-metal');assert m['results'][:len(prior['results'])]==prior['results']
 for k in [k for k in prior if k.endswith('_cpu_regressions')]:
  assert (m[k][:57]==prior[k] and len(m[k])==103) if k=='protection_cpu_regressions' else m[k]==prior[k],k
 roster=load('portable-roster-battles-metal');assert roster['passed'] and len(roster['cases'])==82
 current={(c['character'],c['grown']):case_sha(c) for c in roster['cases']}
 before=old('portable-roster-battles-metal')
 for c in before['cases']:assert current[c['character'],c['grown']]==case_sha(c)
 save('portable-split-roster-parity',dict(passed=True,old_profiles_preserved=74,current_profiles=82,excluded_fields=['cpu_reference_wall_seconds']))
 units={}
 for name,count in {'unit':166,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
  row=next(r for r in g['gates'] if r['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');units[name]=dict(tests=count,output=text)
 save('portable-split-unit-tests',dict(passed=True,groups=units))
 for name,count in (('split',46),('protection',57)):
  native=load('portable-'+name+'-native');assert native['passed'] and len(native['cases'])==count
  for p,h in native['validation_sha256'].items():assert digest(R/p)==h,p
 api=load('portable-api-metal');assert api['passed'] and len(api['split_execution'])==6 and len(api['protection_execution'])==5
 audit=load('portable-catalog-readiness');assert audit['catalog_characters']==203 and audit['own_effect_preflight_passed']==41 and audit['full_character_verified']==0
 assert load('portable-split-storage')['passed']
 if args.pre_optimization:
  save('portable-split-pre-optimization',dict(passed=True,source_commit=source,positive_cases=1479,rejections=294,batched_inputs=1773,unit_tests=166,native_split_cases=46,mac_gates=25,real_profiles=82,windows_report=args.windows_report+'.json',current_full_cuda_batch_executed=True,source_sha256=m['source_sha256'],validation_sha256=m['validation_sha256'],input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],generated_normalized_sha256=normalized,roster_case_hashes=[dict(character=c['character'],grown=c['grown'],sha256=case_sha(c)) for c in roster['cases']]))
  print('All pre-optimization split gates and CUDA transfer verified');return
 decision=load('portable-split-efficiency-decision');assert decision['passed'] and load('portable-split-final-processes')['passed']
 if decision['production_change_adopted']:
  pre=load('portable-split-pre-optimization');assert pre['passed'] and pre['output_sha256']==m['output_sha256']
  for c in pre['roster_case_hashes']:assert current[c['character'],c['grown']]==c['sha256']
  candidate=load('portable-split-candidate-parity');assert candidate['passed'] and candidate['inputs']==1773 and candidate['all_output_bytes_equal']
  for path,h in candidate['parity']['compact']['source_sha256'].items():
   prefix='research/portable-build/split-frame-compact/'
   if path.startswith(prefix+'gpu/'):assert m['source_sha256'][path[len(prefix):]]==h,path
 save('portable-combat-cuda',dict(w,summary_only=True,summary_source=args.windows_report+'.json',scope=m['scope']))
 (P/'portable-combat-v58-checkpoint.json').write_bytes(subprocess.check_output(['git','show','b8ae1c7:research/portable-combat-checkpoint.json'],cwd=R))
 cp=copy.deepcopy(old('portable-combat-checkpoint'));cp.update(wire_abi=hex(ABI),verified_commit=source,previous_checkpoint=dict(report='portable-combat-v58-checkpoint.json',proof_commit='b8ae1c7'),positive_cases=1479,rejections=294,batched_inputs=1773,input_words=L['INPUT_WORDS'],output_words=L['OUTPUT_WORDS'],unit_tests=166,own_effect_preflight_passed=41,real_roster_profiles=82,normal_ui_connected=False,normal_ui_backend='cpu',full_character_verified=0,all_characters_supported=False,full_goal_complete=False,windows_report=args.windows_report+'.json',windows_execution=e,windows_postcheck=post,windows_checks_this_stage=2 if decision['production_change_adopted'] else 1,current_full_cuda_batch_executed=True,source_provenance=dict(fixed_shared_source_commit=source,metal_core_source_commit=source,windows_source_commit=source),validation_receipt='portable-split-validation.json',generated_source_comparison='portable-split-generated-comparison.json',existing_parity='portable-split-existing-metal-parity.json',cuda_verification_mode='full_current_batch',cuda_comparison={k:True for k in keys},regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')},missing_families=audit['missing_families'],splitting=dict(native_cases=46,api_cases=6,ordered_buff_recipients=21,duplicates_preserved=True,only_primary_notifies_received_hit=True,group_frozen_per_primary=True,instant_lists_connected=False,efficiency=decision),next_work=['Connect remaining protection, modifiers, controls, world scheduling and effects; certify all203 characters and variants'])
 for k in ('source_sha256','validation_sha256','input_sha256','output_sha256','batch_layout'):cp[k]=m[k]
 save('portable-combat-checkpoint',cp)
 reports=['portable-combat-metal','portable-combat-cuda','portable-combat-checkpoint','portable-combat-v58-checkpoint',args.windows_report,'portable-split-generated-comparison','portable-split-existing-metal-parity','portable-split-existing-cuda-parity','portable-split-global-gates','portable-split-transfer-completed','portable-split-unit-tests','portable-split-native','portable-split-metal','portable-protection-metal','portable-protection-native','portable-split-storage','portable-split-roster-parity','portable-split-timing-order','portable-split-pre-optimization','portable-split-candidate-parity','portable-split-benchmark','portable-split-efficiency-decision','portable-split-final-processes','portable-split-trace-failure','portable-split-oracle-mask-correction','portable-roster-battles-metal','portable-api-metal','portable-catalog-readiness','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock','portable-duration-extend-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-queue-metal','portable-stack-numeric-metal','portable-stack-notices-metal']
 if decision['production_change_adopted']:reports += ['windows-portable-combat-v59','portable-split-initial-global-gates','portable-split-initial-transfer-completed','portable-split-initial-generated-comparison','portable-split-before-efficiency-metal']
 tools=[P/n for n in ('build-split-cases.py','verify-protection.py','verify-split-regression.py','run-split-gates.py','verify-split-storage.py','split-terminal-check.py','benchmark-split.py','seal-split.py')]
 docs=[R/'docs'/n for n in ('portable-split.md','mac-handoff.md','mac-migration.md','portable-combat-runtime.md')]
 save('portable-split-validation',dict(passed=True,source_commit=source,positive_cases=1479,rejections=294,batched_inputs=1773,unit_tests=166,native_split_cases=46,real_profiles=82,current_full_cuda_batch_executed=True,normal_ui_backend='cpu',full_goal_complete=False,full_character_verified=0,artifact_scope=dict(current_gpu='Common full-core and final source gates',component_gpu='portable-split-metal is the earlier46-case development dispatch; current46 checks are in the common core',diagnostics='Trace/oracle findings retain repaired development issues',world='Authored target/cover masks; automatic boss-world scheduling remains unported'),artifact_sha256={str((P/(n+'.json')).relative_to(R)):digest(P/(n+'.json')) for n in reports},tool_sha256={str(p.relative_to(R)):digest(p) for p in tools},documentation_sha256={str(p.relative_to(R)):digest(p) for p in docs}))
 print('Split proofs sealed; full-catalog GPU goal remains incomplete')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',default='d12b365');a.add_argument('--windows-report',default='windows-portable-combat-v59');a.add_argument('--pre-optimization',action='store_true');args=a.parse_args();main()
