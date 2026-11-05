"""Seal current staged-component evidence; never certify the full catalog."""
import hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';OLD='459465c';SOURCE=None
load=lambda n:json.loads((P/(n+'.json')).read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(P/(n+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def old(n):return json.loads(subprocess.check_output(['git','show',OLD+':research/'+n+'.json'],cwd=R))
def fingerprints(d):
 count=0
 if isinstance(d,dict):
  for key,value in d.items():
   if key.endswith('sha256') and isinstance(value,dict):
    for file,h in value.items():
     if isinstance(h,str) and len(h)==64 and '/' in file and (R/file).is_file():assert sha(R/file)==h,(file,h,sha(R/file));count+=1
   count+=fingerprints(value)
 elif isinstance(d,list):
  for v in d:count+=fingerprints(v)
 return count
m=load('portable-combat-metal');w=load('windows-portable-combat-v38');roster=load('portable-roster-battles-metal');audit=load('portable-catalog-readiness');api=load('portable-api-metal');eq=load('portable-staged-index-equivalence')
SOURCE=w['execution']['commit']
assert subprocess.check_output(['git','show',SOURCE+':research/portable-combat-metal.json'],cwd=R)==(P/'portable-combat-metal.json').read_bytes()
assert m['passed'] and m['gpu_execution_verified'] and len(m['cases'])==1028 and len(m['rejected_cases'])==176
assert len(m['staged_cpu_regressions'])==24
keys=['source_sha256','input_sha256','output_sha256','validation_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
for key in keys:assert w[key]==m[key],key
assert w['passed'] and w['gpu_execution_verified'] and w['backend']=='cuda'
assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
assert w['execution']['commit']==SOURCE and w['execution']['exit_code']==0 and not w['execution']['timed_out']
assert w['postcheck']['remaining_verification_processes']==0
for key in ('head','status'):assert w['postcheck']['original_'+key+'_after']==w['execution']['original_'+key+'_before']
assert roster['passed'] and len(roster['cases'])==52 and all(c['passed'] and not c['differences'] for c in roster['cases'])
assert len(api['staged_execution'])==4 and eq['all_words_equal'] and eq['positive_cases']==1028 and eq['rejections']==176
# Compare old full readbacks; only the newly exposed empty state is removed.
def shape(d):
 return dict(d)
prior=old('portable-combat-metal');current={c['name']:c['actual'] for c in m['cases']}
for c in prior['cases']:assert shape(current[c['name']])==c['actual'],c['name']
prior_roster=old('portable-roster-battles-metal');current_profiles={(c['character'],c['grown'],c['duration']):c for c in roster['cases']}
for c in prior_roster['cases']:
 d=current_profiles[c['character'],c['grown'],c['duration']];assert shape(d['gpu_result'])==c['gpu_result'];assert d['native_reference']==c['native_reference']
save('portable-staged-index-existing-parity',dict(passed=True,baseline_commit=OLD,mechanics=len(prior['cases']),profiles=len(prior_roster['cases']),comparison='Complete decoded equality of every field; metadata ABI changed, no raw input parity claim',current_reports={n:sha(P/(n+'.json')) for n in ('portable-combat-metal','portable-roster-battles-metal')}))
normalized={}
for lang,ext in [('cuda','cu'),('metal','metal')]:
 raw=(P/'portable-build'/('event_runtime.'+ext)).read_bytes();assert hashlib.sha256(raw).hexdigest()==m['generated_sha256'][lang]
 t=raw.decode().replace('\r\n','\n');t='\n'.join(line for line in t.splitlines() if not re.match(r'^\s*#line\b',line))+'\n';t=re.sub(r'"[^"\r\n]*[\\/]slang-cuda-prelude\.h"','"slang-cuda-prelude.h"',t)
 h=hashlib.sha256(t.encode()).hexdigest();assert h==w['generated_normalization'][lang]['no_line_directives_portable_prelude_sha256'];normalized[lang]=h
save('portable-generated-v38-comparison',dict(passed=True,source_commit=SOURCE,gpu_rerun=False,normalization='UTF8/LF, remove #line lines, basename absolute quoted Slang CUDA prelude include',normalized_sha256=normalized))
save('portable-combat-cuda',dict(w,summary_only=True,summary_source='windows-portable-combat-v38.json',scope=m['scope']))
reports=['portable-combat-metal','portable-combat-cuda','windows-portable-combat-v38','portable-staged-index-reference-metal','portable-staged-index-equivalence','portable-roster-battles-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-api-metal','portable-metal-pipeline-lock','portable-numeric-metal','portable-probe-metal','portable-catalog-readiness','portable-staged-index-unit-tests','portable-staged-index-existing-parity','portable-generated-v38-comparison','portable-staged-index-workload-smoke-metal','portable-staged-index-preliminary-timing']+['portable-staged-index-'+str(size)+'-'+label for size in (33,256) for label in ('before','after')]
counts={}
for n in reports:
 d=load(n)
 if n!='portable-catalog-readiness':assert d['passed'],n
 counts[n]=fingerprints(d)
for folder in ('app','scripts'):
 for file in (R/folder).glob('*.py'):assert roster['validation_sha256'][file.relative_to(R).as_posix()]==sha(file),file
benchmarks={}
for size in (33,256):
 before=load('portable-staged-index-'+str(size)+'-before');after=load('portable-staged-index-'+str(size)+'-after')
 assert before['fixture_sha256']==after['fixture_sha256']==sha(R/'tests/fixtures/portable-staged-index-benchmark.json')
 for key in ('input_sha256','output_sha256'):assert before['samples'][0][key]==after['samples'][0][key]
 b=[x['transport']['gpu_seconds'] for x in before['samples']];a=[x['transport']['gpu_seconds'] for x in after['samples']]
 benchmarks[size]=dict(before_median_seconds=before['median_gpu_seconds'],after_median_seconds=after['median_gpu_seconds'],ratio=after['median_gpu_seconds']/before['median_gpu_seconds'],before_range=[min(b),max(b)],after_range=[min(a),max(a)],sample_ranges_overlap=not(max(a)<min(b) or max(b)<min(a)),scope='Bounded synthetic load; unrelated desktop GPU contention not excluded')
cp=dict(wire_abi='0x50455656',verified_commit=SOURCE,source_provenance=dict(fixed_shared_source_commit=SOURCE,metal_core_report_source_commit=SOURCE,windows_source_commit=SOURCE),previous_checkpoint=dict(report='portable-combat-v37-checkpoint.json',proof_commit=OLD),positive_cases=1028,rejections=176,batched_inputs=1204,gpu_dispatches=1,metal_verified=True,cuda_verified=True,metal_report='portable-combat-metal.json',cuda_report='portable-combat-cuda.json',windows_report='windows-portable-combat-v38.json',source_sha256=m['source_sha256'],input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],validation_sha256=m['validation_sha256'],input_words=77824,output_words=69632,normal_ui_connected=False,normal_ui_backend='cpu',all_characters_supported=False,full_goal_complete=False,full_character_verified=0,catalog_characters=203,own_effect_preflight_passed=audit['own_effect_preflight_passed'],weapon_input_preflight_passed=203,weapon_only_metal_verified=203,real_equipment_initialization_squads=203,real_roster_profiles=52,real_fixed_squad=8,unit_tests=94,native_runtime_tests=15,staged_cases=24,staged_api_cases=4,staged_runtime_private_arrays_added=0,staged_runtime_private_scalars_added=5,staged_input_stride_growth_words=0,staged_output_stride_growth_words=0,staged_deadline_formula='start + (index + 1) * gap; software binary64',staged_tie_order='registration sequence',staged_per_frame_limit=4096,staged_zero_count_skips_activation_credit=True,staged_generation_and_carrier_identity_guard=True,cpu_damage_callback_clock_scoped=True,cpu_trace_used_as_gpu_input=False,windows_checks_this_stage=1,windows_execution=w['execution'],windows_postcheck=w['postcheck'],cuda_comparison={k:True for k in keys},generated_source_comparison='portable-generated-v38-comparison.json',validation_receipt='portable-staged-index-validation.json',staged_index_control_all_words_equal=True,staged_index_static_words=257,staged_index_runtime_private_state_growth_words=0,existing_parity='portable-staged-index-existing-parity.json',regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')},missing_families=audit['missing_families'],next_work=['Connect remaining world scheduling, lifecycles and effect families','Certify all 203 characters and all variants before normal UI Metal'])
cp['staged_index_benchmarks']=benchmarks
save('portable-combat-checkpoint',cp)
reports+=['portable-combat-checkpoint','portable-combat-v37-checkpoint']
save('portable-staged-index-validation',dict(passed=True,full_goal_complete=False,source_commit=SOURCE,windows_gpu_runs=1,windows_execution_and_transfer_turn='01a15409-8e1d-7fd0-bed9-21266d01501c',windows_saved_parts=20,windows_saved_only_retry_turn='01a15412-5b3d-7173-b6f5-c09f87ebf2e9',windows_gpu_rerun_for_transfer=False,final_timing_after_all_verification_and_transfers_terminal=True,windows_elapsed_seconds=w['execution']['elapsed_seconds'],current_dependency_counts=counts,artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},benchmark=benchmarks,scope='Indexed staged selection, complete scan/control output equivalence, bounded profiles, one fixed-source CUDA run; no full-catalog or general performance certification'))
print('Sealed staged component:',len(reports),'artifacts; full goal incomplete')
