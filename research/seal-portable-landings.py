"""Seal functional native landing/lifesteal gates, not full-catalog completion."""
import hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';OLD='782659b';SOURCE='431d6998716d2d5d805948a3915df16156b3f3bb'
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
m=load('portable-combat-metal');w=load('windows-portable-combat-v40');roster=load('portable-roster-battles-metal');audit=load('portable-catalog-readiness');api=load('portable-api-metal')
assert subprocess.check_output(['git','show',SOURCE+':research/portable-combat-metal.json'],cwd=R)==(P/'portable-combat-metal.json').read_bytes()
assert m['passed'] and m['gpu_execution_verified'] and len(m['cases'])==1063 and len(m['rejected_cases'])==184
assert len(m['lifesteal_cpu_regressions'])==15 and len(m['landing_cpu_regressions'])==20
keys=['source_sha256','input_sha256','output_sha256','validation_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
for key in keys:assert w[key]==m[key],key
assert w['passed'] and w['gpu_execution_verified'] and w['backend']=='cuda'
assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
assert w['execution']['commit']==SOURCE and w['execution']['exit_code']==0 and not w['execution']['timed_out']
assert w['postcheck']['remaining_verification_processes']==0
for key in ('head','status'):assert w['postcheck']['original_'+key+'_after']==w['execution']['original_'+key+'_before']
assert roster['passed'] and len(roster['cases'])==58 and all(c['passed'] and not c['differences'] for c in roster['cases'])
assert audit['own_effect_preflight_passed']==29 and len(api['landing_execution'])==4
# Preserve old fields exactly; the new native queue diagnostics are separate.
prior=old('portable-combat-metal');current={c['name']:c['actual'] for c in m['cases']}
for c in prior['cases']:
 d=dict(current[c['name']]);q=d.pop('landing_queue');assert q==dict(native=False,enqueued=0,landed=0,drains=0,peak=0,entries=[]);assert d==c['actual'],c['name']
prior_roster=old('portable-roster-battles-metal');current_profiles={(c['character'],c['grown'],c['duration']):c for c in roster['cases']}
for c in prior_roster['cases']:
 d=current_profiles[c['character'],c['grown'],c['duration']];shape=dict(d['gpu_result']);shape.pop('landing_queue');assert shape==c['gpu_result'];assert d['native_reference']==c['native_reference']
save('portable-landings-existing-parity',dict(passed=True,baseline_commit=OLD,mechanics=len(prior['cases']),profiles=len(prior_roster['cases']),comparison='Every old decoded field equal after removing only new landing_queue diagnostics; original CPU references retained; wire dimensions changed, no raw ABI parity claim',current_reports={n:sha(P/(n+'.json')) for n in ('portable-combat-metal','portable-roster-battles-metal')}))
normalized={}
for lang,ext in [('cuda','cu'),('metal','metal')]:
 raw=(P/'portable-build'/('event_runtime.'+ext)).read_bytes();assert hashlib.sha256(raw).hexdigest()==m['generated_sha256'][lang]
 t=raw.decode().replace('\r\n','\n');t='\n'.join(line for line in t.splitlines() if not re.match(r'^\s*#line\b',line))+'\n';t=re.sub(r'"[^"\r\n]*[\\/]slang-cuda-prelude\.h"','"slang-cuda-prelude.h"',t)
 h=hashlib.sha256(t.encode()).hexdigest();assert h==w['generated_normalization'][lang]['no_line_directives_portable_prelude_sha256'];normalized[lang]=h
save('portable-generated-v40-comparison',dict(passed=True,source_commit=SOURCE,gpu_rerun=False,normalization='UTF8/LF, remove #line lines, basename absolute quoted Slang CUDA prelude include',normalized_sha256=normalized))
save('portable-combat-cuda',dict(w,summary_only=True,summary_source='windows-portable-combat-v40.json',scope=m['scope']))
reports=['portable-combat-metal','portable-combat-cuda','windows-portable-combat-v40','portable-roster-battles-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-api-metal','portable-metal-pipeline-lock','portable-numeric-metal','portable-probe-metal','portable-catalog-readiness','portable-landings-unit-tests','portable-landings-existing-parity','portable-generated-v40-comparison','portable-lifesteal-hp-cache-study']
counts={}
for n in reports:
 d=load(n)
 if n!='portable-catalog-readiness':assert d['passed'],n
 counts[n]=fingerprints(d)
for folder in ('app','scripts'):
 for file in (R/folder).glob('*.py'):assert roster['validation_sha256'][file.relative_to(R).as_posix()]==sha(file),file
cp=dict(wire_abi='0x50455657',verified_commit=SOURCE,source_provenance=dict(fixed_shared_source_commit=SOURCE,metal_core_report_source_commit=SOURCE,windows_source_commit=SOURCE),previous_checkpoint=dict(report='portable-combat-v38-checkpoint.json',proof_commit=OLD),prototype_source_commit='27c7438066be03ae3cdd29ce76273ceddcd64d5b',positive_cases=1063,rejections=184,batched_inputs=1247,gpu_dispatches=1,metal_verified=True,cuda_verified=True,metal_report='portable-combat-metal.json',cuda_report='portable-combat-cuda.json',windows_report='windows-portable-combat-v40.json',source_sha256=m['source_sha256'],input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],validation_sha256=m['validation_sha256'],input_words=77824,output_words=98304,normal_ui_connected=False,normal_ui_backend='cpu',all_characters_supported=False,full_goal_complete=False,full_character_verified=0,catalog_characters=203,own_effect_preflight_passed=29,weapon_input_preflight_passed=203,weapon_only_metal_verified=203,real_equipment_initialization_squads=203,real_roster_profiles=58,real_fixed_squad=8,unit_tests=106,native_runtime_tests=15,lifesteal_cases=15,landing_cases=20,landing_api_cases=4,landing_capacity=2048,landing_record_words=12,landing_runtime_private_arrays_added=0,landing_runtime_private_scalars_added=1,landing_frame_fields_added=0,landing_input_stride_growth_words=0,landing_output_stride_growth_words=28672,landing_packets_gpu_owned=True,landing_amount_captured_before_named_callbacks=True,landing_dynamic_tail_drained_in_order=True,b3_recovery_keeps_next_pending_batch=True,normal_landing_after_shot_notifications=True,cpu_hp_numeric_cache_invalidation_corrected=True,original_hp_gap=dict(native=250,prototype=150,current_gpu=250,damage=3000),lifesteal_production_admitted_with_native_phases=True,lifesteal_model_warning_retained=True,cpu_trace_used_as_gpu_input=False,windows_checks_this_stage=1,windows_execution=w['execution'],windows_postcheck=w['postcheck'],cuda_comparison={k:True for k in keys},generated_source_comparison='portable-generated-v40-comparison.json',validation_receipt='portable-landings-validation.json',existing_parity='portable-landings-existing-parity.json',regressions={k:v for k,v in m.items() if k.endswith('_cpu_regressions')},missing_families=audit['missing_families'],next_work=['Compact landing receipt storage and measure queue operations after this functional gate; repeat correctness after changes','Connect remaining world/lifecycle and effect families across all 203 characters','Certify all character variants before normal UI Metal'])
save('portable-combat-checkpoint',cp);reports+=['portable-combat-checkpoint','portable-combat-v38-checkpoint']
save('portable-landings-validation',dict(passed=True,full_goal_complete=False,source_commit=SOURCE,windows_gpu_runs=1,windows_execution_and_transfer_turn='01a1544d-51e9-7410-ad23-3ebf2151b61c',windows_saved_parts=20,windows_elapsed_seconds=w['execution']['elapsed_seconds'],current_dependency_counts=counts,artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},efficiency_measurement_completed=False,scope='Functional shared native receipts/lifesteal, all old mechanics and bounded full-effect profiles, one fixed-source CUDA run; not all-character or all-variant certification; new receipt efficiency work remains'))
print('Sealed native landing functional gates:',len(reports),'artifacts; full goal incomplete')
