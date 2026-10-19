"""Seal v36 owned-source evidence only after all fixed-source gates and timing."""
import hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';OLD='81a6ff5b095e9642569c86a6d82dda389c93ee7c'
load=lambda n:json.loads((P/(n+'.json')).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def old_bytes(name):return subprocess.run(['git','show',OLD+':research/'+name],cwd=R,capture_output=True,check=True).stdout

def fingerprints(value):
 count=0
 if isinstance(value,dict):
  for key,item in value.items():
   if key.endswith('sha256') and isinstance(item,dict):
    for name,h in item.items():
     if isinstance(h,str) and len(h)==64 and '/' in name and (R/name).is_file():assert sha(R/name)==h,(name,h,sha(R/name));count+=1
   count+=fingerprints(item)
 elif isinstance(value,list):
  for item in value:count+=fingerprints(item)
 return count

m=load('portable-combat-metal');w=load('windows-portable-combat-v36');eq=load('portable-sources-equivalence');roster=load('portable-roster-battles-metal');audit=load('portable-catalog-readiness');api=load('portable-api-metal')
assert m['passed'] and len(m['cases'])==1004 and len(m['rejected_cases'])==159
assert len(m['source_cpu_regressions'])==29 and len(m['scale_reference_cpu_regressions'])==40
assert w['passed'] and w['gpu_execution_verified'] and w['backend']=='cuda'
keys=['source_sha256','input_sha256','output_sha256','validation_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
for key in keys:assert w[key]==m[key],key
assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
assert w['execution']['exit_code']==0 and not w['execution']['timed_out'] and w['postcheck']['remaining_verification_processes']==0
assert w['postcheck']['original_head_after']==w['execution']['original_head_before']
assert w['postcheck']['original_status_after']==w['execution']['original_status_before']
commit=w['execution']['commit'];assert subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=R).returncode==0
assert eq['all_words_equal'] and eq['positive_cases']==1004 and eq['rejections']==159
assert roster['passed'] and len(roster['cases'])==52 and all(c['passed'] and not c['differences'] for c in roster['cases'])
assert len(api['source_execution'])==4
# v35 inputs have no owned sources: remove only two new empty readback fields.
def previous_shape(result):
 result=dict(result);assert result.pop('periodic_sources')==[];assert result.pop('source_queries')==[];return result
base=json.loads(old_bytes('portable-combat-metal.json'));current={c['name']:c['actual'] for c in m['cases']}
for case in base['cases']:assert previous_shape(current[case['name']])==case['actual'],case['name']
old_roster=json.loads(old_bytes('portable-roster-battles-metal.json'));current_profiles={(c['character'],c['grown'],c['duration']):c for c in roster['cases']}
for case in old_roster['cases']:
 new=current_profiles[case['character'],case['grown'],case['duration']];assert previous_shape(new['gpu_result'])==case['gpu_result'];assert new['native_reference']==case['native_reference']
parity=dict(passed=True,baseline_commit=OLD,mechanics=len(base['cases']),profiles=len(old_roster['cases']),comparison='Complete decoded equality after removing only empty periodic_sources and source_queries fields; no raw wire parity claim',current_reports={n:sha(P/n) for n in ['portable-combat-metal.json','portable-roster-battles-metal.json']},baseline_reports={n:hashlib.sha256(old_bytes(n)).hexdigest() for n in ['portable-combat-metal.json','portable-roster-battles-metal.json']})
(P/'portable-sources-existing-parity.json').write_text(json.dumps(parity,indent=2)+'\n')
prototype=load('portable-sources-baseline-prototype-metal');assert prototype['passed'] and len(prototype['cases'])==27
for case,result in zip(prototype['cases'],prototype['results']):assert current[case['name']]==result,case['name']
(P/'portable-sources-prototype-parity.json').write_text(json.dumps(dict(passed=True,prototype_cases=27,baseline='portable-sources-baseline-prototype-metal.json',baseline_sha256=sha(P/'portable-sources-baseline-prototype-metal.json'),baseline_scope='Historical uncommitted pre-memoization source snapshot, before CPU numeric invalidation correction; exact complete decoded GPU results compared',comparison='Same externally decoded results across the old eight-word source record and new twelve-word memoized record'),indent=2)+'\n')
# Normalize generated code only for environment-specific textual information.
normalized={}
for language,suffix in [('cuda','cu'),('metal','metal')]:
 raw=(P/'portable-build'/('event_runtime.'+suffix)).read_bytes();assert hashlib.sha256(raw).hexdigest()==m['generated_sha256'][language]
 text=raw.decode('utf-8').replace('\r\n','\n');lines=[line for line in text.splitlines() if not re.match(r'^\s*#line\b',line)];text='\n'.join(lines)+'\n';text=re.sub(r'"[^"\r\n]*[\\/]slang-cuda-prelude\.h"','"slang-cuda-prelude.h"',text)
 h=hashlib.sha256(text.encode()).hexdigest();assert h==w['generated_normalization'][language]['no_line_directives_portable_prelude_sha256'];normalized[language]=dict(raw_sha256=hashlib.sha256(raw).hexdigest(),normalized_sha256=h)
(P/'portable-generated-v36-comparison.json').write_text(json.dumps(dict(passed=True,gpu_rerun=False,source_commit=commit,metal=normalized,windows=w['generated_normalization'],normalization='UTF-8; LF; remove #line lines; basename the absolute quoted Slang CUDA prelude include; computation unchanged'),indent=2)+'\n')
(P/'portable-combat-cuda.json').write_text(json.dumps(dict(w,summary_only=True,summary_source='windows-portable-combat-v36.json',scope=m['scope']),ensure_ascii=False,indent=2)+'\n')
# Timing is allowed only after all functional/transfer handles have ended.
before=load('portable-source-count-benchmark-before');after=load('portable-source-count-benchmark-after')
assert before['passed'] and after['passed'] and before['fixture_sha256']==after['fixture_sha256']
for key in ('input_sha256','output_sha256'):assert before['samples'][0][key]==after['samples'][0][key]
b=[s['transport']['gpu_seconds'] for s in before['samples']];a=[s['transport']['gpu_seconds'] for s in after['samples']]
overlap=not(max(a)<min(b) or max(b)<min(a))
reports=['portable-combat-metal','portable-combat-cuda','portable-sources-reference-metal','portable-sources-equivalence','portable-roster-battles-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-api-metal','portable-metal-pipeline-lock','portable-numeric-metal','portable-probe-metal','portable-catalog-readiness','portable-source-count-workload-smoke-metal','portable-sources-unit-tests','portable-source-count-benchmark-before','portable-source-count-benchmark-after','windows-portable-combat-v36','portable-generated-v36-comparison','portable-sources-existing-parity','portable-sources-prototype-parity','portable-sources-same-time-correction']
counts={}
for name in reports:
 report=load(name)
 if name!='portable-catalog-readiness':assert report['passed'],name
 counts[name]=fingerprints(report)
for folder in ('app','scripts'):
 for file in (R/folder).glob('*.py'):assert roster['validation_sha256'][file.relative_to(R).as_posix()]==sha(file),file
native={name:h for name,h in old_roster['validation_sha256'].items() if name.startswith('research/upstream/')}
for name,h in native.items():assert sha(R/name)==h,name
assert hashlib.sha256(old_bytes('portable-combat-checkpoint.json')).hexdigest()==sha(P/'portable-combat-v35-checkpoint.json')
cp=load('portable-combat-v35-checkpoint');historical={}
for key in list(cp):
 if key.startswith('previous_') or key in ('reference_scaling_equivalence','reference_scaling_validation_receipt','reference_scaling_existing_parity','reference_scaling_unit_report','reference_scaling_benchmark'):historical[key]=cp.pop(key)
cp.update(previous_stage_artifacts=dict(proof_commit=OLD,source_commit=load('portable-combat-v35-checkpoint')['verified_commit'],scope='Historical source-wide receipts; current gates supersede dependency checks',artifacts=historical),wire_abi='0x50455654',verified_commit=commit,previous_checkpoint=dict(report='portable-combat-v35-checkpoint.json',original_checkpoint_commit=OLD),source_provenance=dict(fixed_shared_source_commit=commit,metal_core_report_source_commit=commit,windows_source_commit=commit),positive_cases=1004,rejections=159,batched_inputs=1163,metal_verified=True,cuda_verified=True,source_sha256=m['source_sha256'],input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],validation_sha256=m['validation_sha256'],metal_validation_sha256=m['validation_sha256'],cuda_validation_sha256=w['validation_sha256'],input_words=77824,output_words=69632,windows_report='windows-portable-combat-v36.json',windows_execution=w['execution'],windows_postcheck=w['postcheck'],windows_checks_this_stage=1,cuda_comparison=dict(report='windows-portable-combat-v36.json',all_source_input_output_validation_hashes_match=True,all_case_status_and_reference_lists_match=True),generated_source_comparison='portable-generated-v36-comparison.json',regressions={k.replace('_regressions','_references'):len(v) for k,v in m.items() if k.endswith('_cpu_regressions')},owned_periodic_sources_connected=True,source_reference_cases=29,source_api_cases=4,source_count_capacity=64,source_slot_capacity=32,source_definition_capacity=256,source_owner_first_registration_order=True,source_new_keys_wait_for_next_phase=True,source_later_existing_key_reads_replacement=True,source_current_post_notify_epoch_guard=True,source_expired_zero_presence_retained=True,source_lifetime_binary64_addition=True,source_interval_native_operation_order=True,source_underflowed_interval_first_frame=True,source_count_memo_guard=['exact time bits','refresh epoch'],source_runtime_private_arrays_added=0,source_runtime_private_scalars_added=dict(uint=1,uint64_t=1),source_runtime_allocation_growth_measured=False,source_input_stride_growth_words=20480,source_output_stride_growth_words=4096,source_record_words=12,source_cpu_same_time_numeric_version_fix=True,source_legacy_model_warning_retained=True,source_validation_receipt='portable-sources-validation.json',source_equivalence='portable-sources-equivalence.json',source_existing_parity='portable-sources-existing-parity.json',source_unit_report='portable-sources-unit-tests.json',source_count_benchmark=dict(before=before['median_gpu_seconds'],after=after['median_gpu_seconds'],ratio=after['median_ratio_to_before'],before_samples=b,after_samples=a,sample_ranges_overlap=overlap,clear_local_speedup_observed=not overlap and after['median_gpu_seconds']<before['median_gpu_seconds'],all_output_words_equal=True,strictly_sequential=True,unrelated_desktop_gpu_activity_excluded=False,scope=after['scope']),missing_families=audit['missing_families'],unsupported_damage_definitions=audit['missing_families']['damage'],own_effect_preflight_passed=audit['own_effect_preflight_passed'])
cp['regressions'].update(portable_unit_tests=87,http_source_cases=4,existing_mechanic_parity=975,existing_real_profile_parity=52,pre_memoization_source_cases=27)
cp['real_roster_profiles'].update(candidates=roster['candidates'],required_cases=roster['required_cases'],passed_cases=52,overall_passed=True)
for key in ('known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences'):cp[key]=m[key]
cp['metal_stage_deadlines'].update(cold_compile_report='portable-sources-reference-metal.json',cold_pipeline_compile_seconds=load('portable-sources-reference-metal')['transport']['pipeline_compile_seconds'])
cp['next_work']=['Connect remaining reference-name/condition variants, same-target ramps, world scheduling and remaining effect families','Verify all 203 characters and every authored variant with full real battles before normal UI Metal','Optimize new shared mechanisms after verification with bounded sequential measurements and complete output equality']
assert not cp['full_goal_complete'] and not cp['normal_ui_connected'] and cp['full_character_verified']==0 and cp['normal_ui_backend']=='cpu'
(P/'portable-combat-checkpoint.json').write_text(json.dumps(cp,ensure_ascii=False,indent=2)+'\n')
files=[P/(name+'.json') for name in reports]+[P/'portable-combat-checkpoint.json',P/'portable-combat-v35-checkpoint.json',P/'portable-sources-baseline-prototype-metal.json',Path(__file__).resolve(),R/'docs/portable-sources.md',R/'docs/portable-combat-runtime.md']
receipt=dict(passed=True,verified_code_commit=commit,full_goal_complete=False,full_character_verified=0,normal_ui_connected=False,positive_cases=1004,rejections=159,source_reference_cases=29,portable_unit_tests=87,real_profiles=52,catalog_weapon_cases=203,equipment_squads=203,fixed_battles=8,api_source_cases=4,all_output_words_equal_to_full_counting=True,all_source_input_output_status_reference_lists_equal_cuda_metal=True,windows_gpu_runs=1,windows_execution_and_transfer_turn='01a153dd-6146-7942-817d-11ca92d53352',windows_saved_parts=19,windows_elapsed_seconds=w['execution']['elapsed_seconds'],unchanged_native_source_files=len(native),current_dependency_counts=counts,primitive_reports_rerun_after_transport_stride_change=['portable-numeric-metal.json','portable-probe-metal.json'],existing_parity=parity,benchmark=cp['source_count_benchmark'],artifact_sha256={file.relative_to(R).as_posix():sha(file) for file in files},scope='Shared owned-source components, bounded full-effect profiles, exact cache/control comparison and one fixed-source CUDA run; not all-character/all-variant certification')
(P/'portable-sources-validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print('Sealed v36:',len(files),'artifacts; full goal incomplete')
