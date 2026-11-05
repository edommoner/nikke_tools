"""Seal v35 only after fixed-source Metal/CUDA, global gates and sequential timing."""
import hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';OLD='cdbf2be1a6f8a19fefef0406fd13de508007957e'
load=lambda n:json.loads((P/(n+'.json')).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def git_bytes(name):
 return subprocess.run(['git','show',OLD+':research/'+name],cwd=R,capture_output=True,check=True).stdout

def fingerprint_check(value):
 count=0
 if isinstance(value,dict):
  for k,v in value.items():
   if k.endswith('sha256') and isinstance(v,dict):
    for name,h in v.items():
     if isinstance(h,str) and len(h)==64 and '/' in name and (R/name).is_file():
      assert sha(R/name)==h,(name,h,sha(R/name));count+=1
   count+=fingerprint_check(v)
 elif isinstance(value,list):
  for v in value:count+=fingerprint_check(v)
 return count

m=load('portable-combat-metal');w=load('windows-portable-combat-v35');e=load('portable-reference-scales-equivalence');r=load('portable-roster-battles-metal');a=load('portable-catalog-readiness');api=load('portable-api-metal')
assert len(m['cases'])==975 and len(m['rejected_cases'])==142
assert len(m['scale_reference_cpu_regressions'])==40 and len(m['hit_reference_cpu_regressions'])==37
keys=['source_sha256','input_sha256','output_sha256','validation_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
assert w['passed'] and w['gpu_execution_verified'] and w['backend']=='cuda'
for key in keys:assert m[key]==w[key],key
assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
assert w['execution']['exit_code']==0 and not w['execution']['timed_out']
assert w['postcheck']['remaining_verification_processes']==0
assert w['postcheck']['original_head_after']==w['execution']['original_head_before']
assert w['postcheck']['original_status_after']==w['execution']['original_status_before']
commit=w['execution']['commit'];assert subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=R).returncode==0
assert e['all_words_equal'] and e['positive_cases']==975 and e['rejections']==142
assert r['passed'] and len(r['cases'])==52 and all(c['passed'] and not c['differences'] for c in r['cases'])
assert len(api['scale_reference_execution'])==4
# Previous wire layout gained only an empty decoded field for prior inputs.
base=json.loads(git_bytes('portable-combat-metal.json'));rows={c['name']:c['actual'] for c in m['cases']}
for c in base['cases']:
 actual=dict(rows[c['name']]);assert actual.pop('reference_captures')==[];assert actual==c['actual'],c['name']
base_roster=json.loads(git_bytes('portable-roster-battles-metal.json'));rows={(c['character'],c['grown'],c['duration']):c for c in r['cases']}
for c in base_roster['cases']:
 current=rows[c['character'],c['grown'],c['duration']];actual=dict(current['gpu_result']);assert actual.pop('reference_captures')==[];assert actual==c['gpu_result'];assert current['native_reference']==c['native_reference']
parity=dict(passed=True,baseline_commit=OLD,mechanics=len(base['cases']),profiles=len(base_roster['cases']),comparison='Complete decoded result equality after removing only the newly added empty reference_captures field; no raw wire hash parity claim',current_reports={n:sha(P/n) for n in ['portable-combat-metal.json','portable-roster-battles-metal.json']},baseline_reports={n:hashlib.sha256(git_bytes(n)).hexdigest() for n in ['portable-combat-metal.json','portable-roster-battles-metal.json']})
(P/'portable-reference-scales-existing-parity.json').write_text(json.dumps(parity,indent=2)+'\n')
# Only line directives, line endings and the Slang CUDA prelude path normalize.
local={}
for language,suffix in [('cuda','cu'),('metal','metal')]:
 raw=(P/'portable-build'/('event_runtime.'+suffix)).read_bytes();assert hashlib.sha256(raw).hexdigest()==m['generated_sha256'][language]
 text=raw.decode('utf-8').replace('\r\n','\n');lines=text.splitlines();filtered=[s for s in lines if not re.match(r'^\s*#line\b',s)];normalized='\n'.join(filtered)+'\n';normalized=re.sub(r'"[^"\r\n]*[\\/]slang-cuda-prelude\.h"','"slang-cuda-prelude.h"',normalized)
 h=hashlib.sha256(normalized.encode()).hexdigest();assert h==w['generated_normalization'][language]['no_line_directives_portable_prelude_sha256']
 local[language]=dict(raw_sha256=hashlib.sha256(raw).hexdigest(),no_line_directives_portable_prelude_sha256=h)
(P/'portable-generated-v35-comparison.json').write_text(json.dumps(dict(passed=True,gpu_rerun=False,source_commit=commit,metal=local,windows=w['generated_normalization'],normalization='UTF-8, LF, remove #line, basename only for absolute quoted slang-cuda-prelude.h include; no computation rewrite'),indent=2)+'\n')
cuda=dict(w,summary_only=True,summary_source='windows-portable-combat-v35.json',scope=m['scope']);(P/'portable-combat-cuda.json').write_text(json.dumps(cuda,ensure_ascii=False,indent=2)+'\n')
before=load('portable-reference-scale-benchmark-before');after=load('portable-reference-scale-benchmark-after');assert before['passed'] and after['passed'];assert before['samples'][0]['input_sha256']==after['samples'][0]['input_sha256'];assert before['samples'][0]['output_sha256']==after['samples'][0]['output_sha256'];assert before['fixture_sha256']==after['fixture_sha256']
reports=['portable-combat-metal','portable-combat-cuda','portable-reference-scales-reference-metal','portable-reference-scales-equivalence','portable-roster-battles-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-api-metal','portable-metal-pipeline-lock','portable-numeric-metal','portable-probe-metal','portable-catalog-readiness','portable-reference-scale-workload-smoke-metal','portable-reference-scales-unit-tests','portable-reference-health-boundaries-metal','portable-reference-health-gpu-study','portable-reference-scale-benchmark-before','portable-reference-scale-benchmark-after','windows-portable-combat-v35','portable-generated-v35-comparison','portable-reference-scales-existing-parity']
counts={}
for name in reports:
 d=load(name)
 if name!='portable-catalog-readiness':assert d['passed'],name
 counts[name]=fingerprint_check(d)
for folder in ('app','scripts'):
 for p in (R/folder).glob('*.py'):assert r['validation_sha256'][p.relative_to(R).as_posix()]==sha(p),p
native={n:h for n,h in base_roster['validation_sha256'].items() if n.startswith('research/upstream/')}
for n,h in native.items():assert sha(R/n)==h,n
cp=load('portable-combat-v34-checkpoint');assert sha(P/'portable-combat-v34-checkpoint.json')==hashlib.sha256(git_bytes('portable-combat-checkpoint.json')).hexdigest()
# Historical source-wide receipts remain explicitly tied to their proof commit.
previous={}
for key in list(cp):
 if key.startswith('previous_') or key in ['unchanged_prior_verifications','resource_native_witness','resource_initial_compiler_failures','hit_reference_native_AST_witness','hit_reference_unit_report','hit_reference_existing_parity','hit_reference_expectation_corrections','hit_reference_validation_receipt','hit_reference_equivalence','hit_reference_benchmark','hit_reference_stress_benchmark','hit_reference_measurement_audit','hit_reference_normal_benchmark_final_damage_audit']:previous[key]=cp.pop(key)
cp.update(previous_stage_artifacts=dict(proof_commit=OLD,source_commit=load('portable-combat-v34-checkpoint')['verified_commit'],scope='Historical records; current shared fixtures/profile gates supersede source-wide fingerprints',artifacts=previous),wire_abi='0x50455653',verified_commit=commit,previous_checkpoint=dict(report='portable-combat-v34-checkpoint.json',original_checkpoint_commit=OLD),source_provenance=dict(fixed_shared_source_commit=commit,metal_core_report_source_commit=commit,windows_source_commit=commit),positive_cases=975,rejections=142,batched_inputs=1117,source_sha256=m['source_sha256'],input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],validation_sha256=m['validation_sha256'],metal_validation_sha256=m['validation_sha256'],cuda_validation_sha256=w['validation_sha256'],windows_report='windows-portable-combat-v35.json',windows_execution=w['execution'],windows_postcheck=w['postcheck'],windows_checks_this_stage=1,metal_verified=True,cuda_verified=True,cuda_comparison=dict(report='windows-portable-combat-v35.json',all_source_input_output_validation_hashes_match=True,all_case_status_and_reference_lists_match=True),generated_source_comparison='portable-generated-v35-comparison.json',regressions={k.replace('_regressions','_references'):len(v) for k,v in m.items() if k.endswith('_cpu_regressions')},reference_scaling_connected=True,reference_scaling_cases=40,reference_scaling_api_cases=4,reference_scaling_finite_capture_refresh_order=True,reference_scaling_dot_signed_and_large_capture=True,reference_scaling_maximum_hp_boundary_sync=True,reference_scaling_cpu_cache_correction=True,reference_scaling_capture_words=1536,reference_scaling_runtime_private_arrays_added=0,reference_scaling_input_stride_growth_words=0,reference_scaling_output_stride_growth_words=0,reference_scaling_equivalence='portable-reference-scales-equivalence.json',reference_scaling_validation_receipt='portable-reference-scales-validation.json',reference_scaling_existing_parity='portable-reference-scales-existing-parity.json',reference_scaling_unit_report='portable-reference-scales-unit-tests.json',reference_scaling_benchmark=dict(before=before['median_gpu_seconds'],after=after['median_gpu_seconds'],ratio=after['median_ratio_to_before'],scope=after['scope'],all_output_words_equal=True,strictly_sequential=True,unrelated_desktop_gpu_activity_excluded=False),unsupported_damage_definitions=a['missing_families']['damage'],missing_families=a['missing_families'],own_effect_preflight_passed=a['own_effect_preflight_passed'])
cp['reference_scaling_benchmark'].update(clear_speedup_proven=False,sample_ranges_overlap=True,before_samples=[s['transport']['gpu_seconds'] for s in before['samples']],after_samples=[s['transport']['gpu_seconds'] for s in after['samples']])
cp['metal_stage_deadlines'].update(cold_compile_report='portable-reference-health-gpu-study.json',cold_pipeline_compile_seconds=load('portable-reference-health-gpu-study')['transport']['pipeline_compile_seconds'])
cp['regressions'].update(portable_unit_tests=80,http_reference_scale_cases=4,existing_mechanic_parity=935,existing_real_profile_parity=52)
cp['real_roster_profiles'].update(candidates=r['candidates'],required_cases=r['required_cases'],passed_cases=len(r['cases']),overall_passed=True)
for key in ('known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences'):cp[key]=m[key]
cp['next_work']=['Connect feather live counts, same-target ramps and remaining world/effect families to the shared executor','Verify all 203 characters and every authored variant with full real battles before normal UI Metal','Optimize new shared mechanisms only after full verification, using sequential bounded measurements with output equality']
assert not cp['full_goal_complete'] and not cp['normal_ui_connected'] and cp['full_character_verified']==0 and cp['normal_ui_backend']=='cpu'
(P/'portable-combat-checkpoint.json').write_text(json.dumps(cp,ensure_ascii=False,indent=2)+'\n')
files=[P/(n+'.json') for n in reports]+[P/'portable-combat-checkpoint.json',P/'portable-combat-v34-checkpoint.json',Path(__file__).resolve(),R/'docs/portable-reference-scales.md',R/'docs/portable-combat-runtime.md']
receipt=dict(passed=True,verified_code_commit=commit,full_goal_complete=False,full_character_verified=0,normal_ui_connected=False,positive_cases=975,rejections=142,reference_scaling_cases=40,portable_unit_tests=80,real_profiles=52,catalog_weapon_cases=203,equipment_squads=203,fixed_battles=8,api_reference_scale_cases=4,all_output_words_equal_to_always_lookup=True,all_source_input_output_status_reference_lists_equal_cuda_metal=True,windows_gpu_runs=1,windows_elapsed_seconds=w['execution']['elapsed_seconds'],unchanged_native_source_files=len(native),current_dependency_counts=counts,primitive_reports_revalidated_without_gpu_rerun=['portable-numeric-metal.json','portable-probe-metal.json'],existing_parity=parity,benchmark=cp['reference_scaling_benchmark'],artifact_sha256={p.relative_to(R).as_posix():sha(p) for p in files},scope='Shared components, bounded full-effect profiles and one fixed-source CUDA run; not all-character or all-variant certification')
(P/'portable-reference-scales-validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print('Sealed v35:',len(files),'artifacts; full goal incomplete')
