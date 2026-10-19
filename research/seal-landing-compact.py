"""Seal fixed-source shared compact receipts after global gates and timing."""
import hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='70f90181245ff1ca5d0930bc2e332762d99ebde1';OLD='60c53bc'
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
m=load('portable-combat-metal');w=load('windows-portable-combat-v41');roster=load('portable-roster-battles-metal');audit=load('portable-catalog-readiness');api=load('portable-api-metal');batch=load('portable-landing-compact-batch-metal');live=load('portable-landing-compact-metal')
assert subprocess.check_output(['git','show',SOURCE+':research/portable-combat-metal.json'],cwd=R)==(P/'portable-combat-metal.json').read_bytes()
assert m['passed'] and m['gpu_execution_verified'] and len(m['cases'])==1063 and len(m['rejected_cases'])==184
keys=['source_sha256','input_sha256','output_sha256','validation_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
for key in keys:assert w[key]==m[key],key
assert w['passed'] and w['gpu_execution_verified'] and w['backend']=='cuda'
assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
assert w['execution']['commit']==SOURCE and w['execution']['exit_code']==0 and not w['execution']['timed_out']
assert w['postcheck']['remaining_verification_processes']==0
for key in ('head','status'):assert w['postcheck']['original_'+key+'_after']==w['execution']['original_'+key+'_before']
codec=w['landing_codec']
if 'codec' in codec:codec=codec['codec']
assert codec['passed'] and codec['valid_vectors']==259 and codec['invalid_vectors']==11
for key in ('source_sha256','input_sha256','output_sha256'):assert codec[key]==batch['codec'][key],key
assert batch['passed'] and batch['batched_inputs']==1247 and batch['canonical_output_sha256']==m['output_sha256']
assert live['passed'] and live['live_queue_decoder_verified']
assert roster['passed'] and len(roster['cases'])==58 and all(c['passed'] and not c['differences'] for c in roster['cases'])
assert audit['own_effect_preflight_passed']==29 and len(api['landing_execution'])==4
assert old('portable-combat-metal')['cases']==m['cases']
prior=old('portable-roster-battles-metal');current={(c['character'],c['grown'],c['duration']):c for c in roster['cases']}
for c in prior['cases']:
 d=current[c['character'],c['grown'],c['duration']];assert d['gpu_result']==c['gpu_result'];assert d['native_reference']==c['native_reference']
save('portable-landing-compact-existing-parity',dict(passed=True,baseline_commit=OLD,mechanics=1063,profiles=58,comparison='Every decoded field and original CPU reference identical, including queue diagnostics; no raw old-ABI equality claim',current_reports={n:sha(P/(n+'.json')) for n in ('portable-combat-metal','portable-roster-battles-metal')}))
normalized={}
for lang,ext in [('cuda','cu'),('metal','metal')]:
 raw=(P/'portable-build'/('event_runtime.'+ext)).read_bytes();assert hashlib.sha256(raw).hexdigest()==m['generated_sha256'][lang]
 t=raw.decode().replace('\r\n','\n');t='\n'.join(line for line in t.splitlines() if not re.match(r'^\s*#line\b',line))+'\n';t=re.sub(r'"[^"\r\n]*[\\/]slang-cuda-prelude\.h"','"slang-cuda-prelude.h"',t)
 h=hashlib.sha256(t.encode()).hexdigest();assert h==w['generated_normalization'][lang]['no_line_directives_portable_prelude_sha256'];normalized[lang]=h
save('portable-generated-v41-comparison',dict(passed=True,source_commit=SOURCE,gpu_rerun=False,normalized_sha256=normalized))
save('portable-combat-cuda',dict(w,summary_only=True,summary_source='windows-portable-combat-v41.json',scope=m['scope']))
order=load('portable-landing-compact-timing-order');assert order['passed'] and not order['verification_processes'] and order['windows_execution_and_transfer_terminal']
timings={}
for workload in ('two-receipts','full-2048'):
 a=load('portable-landing-'+workload+'-wide-benchmark');b=load('portable-landing-'+workload+'-compact-benchmark')
 assert a['passed'] and b['passed'] and a['samples'][0]['canonical_output_sha256']==b['samples'][0]['canonical_output_sha256']
 timings[workload]=dict(wide_gpu_seconds=a['median_gpu_seconds'],compact_gpu_seconds=b['median_gpu_seconds'],ratio=b['median_ratio_to_wide'])
reports=['portable-combat-metal','portable-combat-cuda','windows-portable-combat-v41','portable-roster-battles-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-api-metal','portable-metal-pipeline-lock','portable-numeric-metal','portable-probe-metal','portable-catalog-readiness','portable-landing-compact-unit-tests','portable-landing-compact-existing-parity','portable-generated-v41-comparison','portable-landing-compact-metal','portable-landing-compact-batch-metal','portable-landing-compact-memory','portable-landing-compact-timing-order','portable-landing-compact-transfer-completed']+['portable-landing-'+w+'-'+l+'-benchmark' for w in ('two-receipts','full-2048') for l in ('wide','compact')]
counts={}
for n in reports:
 d=load(n)
 if n!='portable-catalog-readiness':assert d['passed'],n
 counts[n]=fingerprints(d)
for folder in ('app','scripts'):
 for file in (R/folder).glob('*.py'):assert roster['validation_sha256'][file.relative_to(R).as_posix()]==sha(file),file
cp=old('portable-combat-checkpoint')
cp.update(wire_abi='0x50455658',verified_commit=SOURCE,source_provenance=dict(fixed_shared_source_commit=SOURCE,metal_core_report_source_commit=SOURCE,windows_source_commit=SOURCE),previous_checkpoint=dict(report='portable-combat-v40-checkpoint.json',proof_commit=OLD),source_sha256=m['source_sha256'],input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],validation_sha256=m['validation_sha256'],output_words=90112,windows_report='windows-portable-combat-v41.json',windows_execution=w['execution'],windows_postcheck=w['postcheck'],cuda_comparison={k:True for k in keys},generated_source_comparison='portable-generated-v41-comparison.json',validation_receipt='portable-landing-compact-validation.json',existing_parity='portable-landing-compact-existing-parity.json',landing_record_words=8,landing_output_stride_growth_words=20480,landing_bytes_saved_per_program=32768,landing_pool_bytes_before=98304,landing_pool_bytes_after=65536,landing_output_reduction_fraction=1/12,landing_codec_valid_vectors=259,landing_codec_invalid_vectors=11,landing_wide_compact_all_output_words_equal=True,landing_live_queue_decoder_verified=True,landing_compact_timings=timings,next_work=['Connect remaining lifecycle/recipient/world and effect families across all 203 characters','Certify all character variants before normal UI Metal'])
save('portable-combat-checkpoint',cp);reports+=['portable-combat-checkpoint','portable-combat-v40-checkpoint']
save('portable-landing-compact-validation',dict(passed=True,full_goal_complete=False,source_commit=SOURCE,windows_gpu_runs_of_bounded_wrapper=1,windows_elapsed_seconds=w['execution']['elapsed_seconds'],current_dependency_counts=counts,artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},efficiency_measurement_completed=True,bytes_saved_per_program=32768,timings=timings,scope='Lossless shared receipt layout, same full tested physics, bounded sequential timings; not full-catalog or all-variant certification'))
print('Sealed compact landing gates:',len(reports),'artifacts; full goal incomplete')
