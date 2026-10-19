"""Seal current staged-component evidence; never certify the full catalog."""
import hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';OLD='4f3cef4';SOURCE='8bc3c97a2247f7b84113894cc1fbd6d9ac368086'
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
m=load('portable-combat-metal');w=load('windows-portable-combat-v37');roster=load('portable-roster-battles-metal');audit=load('portable-catalog-readiness');api=load('portable-api-metal');eq=load('portable-sources-equivalence')
assert m['passed'] and m['gpu_execution_verified'] and len(m['cases'])==1027 and len(m['rejected_cases'])==171
assert len(m['staged_cpu_regressions'])==23
keys=['source_sha256','input_sha256','output_sha256','validation_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
for key in keys:assert w[key]==m[key],key
assert w['passed'] and w['gpu_execution_verified'] and w['backend']=='cuda'
assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
assert w['execution']['commit']==SOURCE and w['execution']['exit_code']==0 and not w['execution']['timed_out']
assert w['postcheck']['remaining_verification_processes']==0
for key in ('head','status'):assert w['postcheck']['original_'+key+'_after']==w['execution']['original_'+key+'_before']
assert roster['passed'] and len(roster['cases'])==52 and all(c['passed'] and not c['differences'] for c in roster['cases'])
assert len(api['staged_execution'])==4 and eq['all_words_equal'] and eq['positive_cases']==1027 and eq['rejections']==171
# Compare old full readbacks; only the newly exposed empty state is removed.
def shape(d):
 d=dict(d);assert d.pop('staged_applications')==[];return d
prior=old('portable-combat-metal');current={c['name']:c['actual'] for c in m['cases']}
for c in prior['cases']:assert shape(current[c['name']])==c['actual'],c['name']
prior_roster=old('portable-roster-battles-metal');current_profiles={(c['character'],c['grown'],c['duration']):c for c in roster['cases']}
for c in prior_roster['cases']:
 d=current_profiles[c['character'],c['grown'],c['duration']];assert shape(d['gpu_result'])==c['gpu_result'];assert d['native_reference']==c['native_reference']
save('portable-staged-existing-parity',dict(passed=True,baseline_commit=OLD,mechanics=len(prior['cases']),profiles=len(prior_roster['cases']),comparison='Complete decoded equality after removing only the new empty staged_applications field; no raw ABI parity claim',current_reports={n:sha(P/(n+'.json')) for n in ('portable-combat-metal','portable-roster-battles-metal')}))
normalized={}
for lang,ext in [('cuda','cu'),('metal','metal')]:
 raw=(P/'portable-build'/('event_runtime.'+ext)).read_bytes();assert hashlib.sha256(raw).hexdigest()==m['generated_sha256'][lang]
 t=raw.decode().replace('\r\n','\n');t='\n'.join(line for line in t.splitlines() if not re.match(r'^\s*#line\b',line))+'\n';t=re.sub(r'"[^"\r\n]*[\\/]slang-cuda-prelude\.h"','"slang-cuda-prelude.h"',t)
 h=hashlib.sha256(t.encode()).hexdigest();assert h==w['generated_normalization'][lang]['no_line_directives_portable_prelude_sha256'];normalized[lang]=h
save('portable-generated-v37-comparison',dict(passed=True,source_commit=SOURCE,gpu_rerun=False,normalization='UTF8/LF, remove #line lines, basename absolute quoted Slang CUDA prelude include',normalized_sha256=normalized))
save('portable-combat-cuda',dict(w,summary_only=True,summary_source='windows-portable-combat-v37.json',scope=m['scope']))
reports=['portable-combat-metal','portable-combat-cuda','windows-portable-combat-v37','portable-sources-reference-metal','portable-sources-equivalence','portable-roster-battles-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-api-metal','portable-metal-pipeline-lock','portable-numeric-metal','portable-probe-metal','portable-catalog-readiness','portable-staged-unit-tests','portable-staged-existing-parity','portable-generated-v37-comparison']
counts={}
for n in reports:
 d=load(n)
 if n!='portable-catalog-readiness':assert d['passed'],n
 counts[n]=fingerprints(d)
for folder in ('app','scripts'):
 for file in (R/folder).glob('*.py'):assert roster['validation_sha256'][file.relative_to(R).as_posix()]==sha(file),file
cp=dict(wire_abi='0x50455655',verified_commit=SOURCE,source_provenance=dict(fixed_shared_source_commit=SOURCE,metal_core_report_source_commit=SOURCE,windows_source_commit=SOURCE),previous_checkpoint=dict(report='portable-combat-v36-checkpoint.json',proof_commit=OLD),positive_cases=1027,rejections=171,batched_inputs=1198,gpu_dispatches=1,metal_verified=True,cuda_verified=True,metal_report='portable-combat-metal.json',cuda_report='portable-combat-cuda.json',windows_report='windows-portable-combat-v37.json',source_sha256=m['source_sha256'],input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],validation_sha256=m['validation_sha256'],input_words=77824,output_words=69632,normal_ui_connected=False,normal_ui_backend='cpu',all_characters_supported=False,full_goal_complete=False,full_character_verified=0,catalog_characters=203,own_effect_preflight_passed=audit['own_effect_preflight_passed'],weapon_input_preflight_passed=203,weapon_only_metal_verified=203,real_equipment_initialization_squads=203,real_roster_profiles=52,real_fixed_squad=8,unit_tests=93,native_runtime_tests=15,staged_cases=23,staged_api_cases=4,staged_runtime_private_arrays_added=0,staged_runtime_private_scalars_added=5,staged_input_stride_growth_words=0,staged_output_stride_growth_words=0,staged_deadline_formula='start + (index + 1) * gap; software binary64',staged_tie_order='registration sequence',staged_per_frame_limit=4096,staged_zero_count_skips_activation_credit=True,staged_generation_and_carrier_identity_guard=True,cpu_damage_callback_clock_scoped=True,cpu_trace_used_as_gpu_input=False,windows_checks_this_stage=1,windows_execution=w['execution'],windows_postcheck=w['postcheck'],cuda_comparison={k:True for k in keys},generated_source_comparison='portable-generated-v37-comparison.json',validation_receipt='portable-staged-validation.json',source_cache_control_all_words_equal=True,existing_parity='portable-staged-existing-parity.json',regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')},missing_families=audit['missing_families'],next_work=['Measure and optimize the staged scheduler after correctness; no staged speedup claim in this receipt','Connect remaining world scheduling, lifecycles and effect families','Certify all 203 characters and all variants before normal UI Metal'])
save('portable-combat-checkpoint',cp)
reports+=['portable-combat-checkpoint','portable-combat-v36-checkpoint']
save('portable-staged-validation',dict(passed=True,full_goal_complete=False,source_commit=SOURCE,windows_gpu_runs=1,windows_execution_and_transfer_turn='01a153fa-4e24-7853-af40-35653e00c670',windows_saved_parts=20,windows_elapsed_seconds=w['execution']['elapsed_seconds'],current_dependency_counts=counts,artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},scope='Shared staged components, existing weapons/bursts/targets, bounded profiles, one fixed-source CUDA run; no full-catalog or performance certification'))
print('Sealed staged component:',len(reports),'artifacts; full goal incomplete')
