"""Seal the foundation, preserving explicit incomplete all-character status."""
import copy,hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research'
SOURCE='6e28e63d65c9109b56480782b053b2dddf44b71f'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(raw):
 text=raw.decode().replace('\r\n','\n').replace('\r','\n')
 text='\n'.join(x for x in text.split('\n') if not re.match(r'^\s*#line\b',x))
 text=re.sub(r'"([^"\n]+)"',lambda m:'"'+m[1].replace('\\','/').split('/')[-1]+'"' if '/' in m[1] or '\\' in m[1] or m[1]=='slang-cuda-prelude.h' else m[0],text)
 return hashlib.sha256(text.encode()).hexdigest()
def main():
 m=load('portable-combat-metal');w=load('windows-portable-combat-v50');g=load('portable-stack-increment-global-gates');t=load('portable-stack-increment-transfer-completed')
 assert m['passed'] and len(m['cases'])==1149 and len(m['rejected_cases'])==206
 assert len(m['mode_session_cpu_regressions'])==41 and m['known_mode_cpu_differences']==[]
 assert g['passed'] and g['complete'] and len(g['gates'])==22
 assert t['passed'] and t['remote_turn_status']=='completed' and t['parts']==t['total_parts']
 assert w['passed'] and w['gpu_execution_verified'] and w['execution']['commit']==SOURCE
 e=w['execution'];assert e['exit_code']==0 and not e['timed_out'] and e['below_normal_priority'] and e['timeout_seconds']==120
 assert w['postcheck']['remaining_verification_processes']==0
 for k in ('head','status'):assert w['postcheck']['original_'+k+'_after']==e['original_'+k+'_before']
 keys=['source_sha256','input_sha256','output_sha256','validation_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']+[k for k in m if k.endswith('_cpu_regressions')]
 for k in keys:assert m[k]==w[k],k
 assert w['cases']==[dict(name=c['name'],passed=c['passed']) for c in m['cases']]
 for k in ('source_sha256','validation_sha256'):
  for p,h in m[k].items():assert sha(R/p)==h,p
 generated={}
 for backend,suffix in [('cuda','cu'),('metal','metal')]:
  p=P/'portable-build'/('event_runtime.'+suffix);assert sha(p)==m['generated_sha256'][backend]
  generated[backend]=normalized(p.read_bytes());assert generated[backend]==w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
 for name,count,remote in [('numeric',19908,'stack_numeric'),('notices',9,'stack_notices')]:
  a=load('portable-stack-'+name+'-metal');b=w[remote];assert a['passed'] and b['passed']
  assert (a['cases'] if name=='numeric' else len(a['cases']))==count
  for k in ('input_sha256','output_sha256','source_sha256','cases'):assert a[k]==b[k],(name,k)
  for p,h in a['source_sha256'].items():assert sha(R/p)==h
  save('portable-stack-'+name+'-cuda',b)
 for backend in ('metal','cuda'):
  p=load('portable-stack-increment-existing-'+backend+'-parity');assert p['passed'] and p['inputs']==1355 and p['all_input_and_output_bytes_equal'] and p['no_input_or_output_normalization']
  for k in ('source_sha256','input_sha256','output_sha256'):assert p[k]==m[k]
 old=json.loads(subprocess.check_output(['git','show','7d52456:research/portable-combat-metal.json'],cwd=R))
 assert m['results']==old['results']
 roster=load('portable-roster-battles-metal');prior=json.loads(subprocess.check_output(['git','show','7d52456:research/portable-roster-battles-metal.json'],cwd=R))
 strip=lambda c:{k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'}
 assert roster['passed'] and len(roster['cases'])==58
 assert [strip(c) for c in roster['cases']]==[strip(c) for c in prior['cases']]
 unit={}
 for name,count in {'unit':131,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
  row=next(r for r in g['gates'] if r['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');unit[name]=dict(tests=count,output=text)
 save('portable-stack-increment-unit-tests',dict(passed=True,groups=unit))
 save('portable-generated-v50-comparison',dict(passed=True,source_commit=SOURCE,compared_keys=keys,normalized_sha256=generated))
 save('portable-combat-cuda',dict(w,summary_only=True,summary_source='windows-portable-combat-v50.json',scope=m['scope']))
 prior_cp=json.loads(subprocess.check_output(['git','show','7d52456:research/portable-combat-checkpoint.json'],cwd=R));save('portable-combat-v49-checkpoint',prior_cp)
 cp=copy.deepcopy(prior_cp);cp.update(historical_measurement_scope='Inherited landing/definition/mode/session metrics retain their original proof provenance; they are not fresh timing measurements at this source.',wire_abi='0x50455661',input_words=77824,output_words=94208,batch_layout=m['batch_layout'],verified_commit=SOURCE,source_provenance=dict(fixed_shared_source_commit=SOURCE,metal_core_report_source_commit=SOURCE,windows_source_commit=SOURCE),
  previous_checkpoint=dict(report='portable-combat-v49-checkpoint.json',proof_commit='7d52456'),windows_report='windows-portable-combat-v50.json',windows_checks_this_stage=1,windows_checks_foundation_and_specialization=2,stack_increment_specialization_adopted=True,stack_increment_measurement='portable-stack-increment-benchmark.json',windows_execution=e,windows_postcheck=w['postcheck'],
  validation_receipt='portable-stack-increment-validation.json',generated_source_comparison='portable-generated-v50-comparison.json',existing_parity='portable-stack-increment-existing-metal-parity.json',
  stack_foundation=dict(abi='0x50455661',input_words=77824,output_words=94208,added_output_bytes=16384,numeric_cases=19908,notice_cases=9,added_private_arrays=0,added_runtime_scalars=0,new_effect_kinds_admitted=False),
  normal_ui_backend='cpu',normal_ui_connected=False,full_goal_complete=False,full_character_verified=0,all_characters_supported=False,
  next_work=['Connect stack mutation/init/immunity effects using the documented native contract','Complete remaining lifecycle/world/control/effect families and certify all variants'])
 for k in ('source_sha256','input_sha256','output_sha256','validation_sha256'):cp[k]=m[k]
 save('portable-combat-checkpoint',cp)
 reports=['portable-combat-metal','portable-combat-cuda','windows-portable-combat-v50','portable-generated-v50-comparison','portable-stack-increment-existing-metal-parity','portable-stack-increment-existing-cuda-parity','portable-stack-increment-global-gates','portable-stack-increment-transfer-completed','portable-stack-increment-unit-tests','portable-stack-increment-timing-order','portable-stack-increment-adoption','portable-stack-numeric-metal','portable-stack-numeric-cuda','portable-stack-notices-metal','portable-stack-notices-cuda','portable-stack-notice-probe-repair','portable-stack-native-contract','portable-stack-enemy-contract','portable-stack-initialization-contract','portable-combat-checkpoint','portable-roster-battles-metal','portable-api-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock','portable-duration-extend-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-queue-metal','portable-catalog-readiness']
 assert load('portable-stack-native-contract')['passed'] and len(load('portable-stack-native-contract')['cases'])==53
 assert load('portable-stack-enemy-contract')['passed'] and len(load('portable-stack-enemy-contract')['observations'])==22
 assert load('portable-stack-initialization-contract')['passed'] and len(load('portable-stack-initialization-contract')['cases'])==11
 audit=load('portable-catalog-readiness');assert audit['catalog_characters']==203 and audit['own_effect_preflight_passed']==29 and audit['full_character_verified']==0
 adoption=load('portable-stack-increment-adoption');assert adoption['passed'] and adoption['production_change_adopted']
 bench=P/'portable-stack-increment-benchmark.json'
 if bench.exists():
  b=load('portable-stack-increment-benchmark');assert b['passed'] and b['production_change_adopted'] is False
  assert b['production_source_sha256']==old['source_sha256'];reports.append('portable-stack-increment-benchmark')
 save('portable-stack-increment-validation',dict(passed=True,source_commit=SOURCE,positive_cases=1149,rejections=206,native_mode_cases=41,unit_tests=131,real_profiles=58,numeric_stack_cases=19908,notice_cases=9,new_effect_kinds_admitted=False,full_goal_complete=False,full_character_verified=0,native_stack_contract_cases=53,native_enemy_contract_observations=22,native_initialization_contract_cases=11,windows_runs=1,windows_runs_foundation_and_specialization=2,efficiency_specialization_adopted=True,artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},tool_sha256={str(p.relative_to(R)):sha(p) for p in [P/'verify-stack-foundation.py',P/'verify-stack-increment-existing.py',P/'run-stack-increment-gates.py',P/'benchmark-stack-increment.py',P/'seal-stack-increment.py',P/'verify-stack-native-contract.py',P/'verify-stack-enemy-contract.py',P/'verify-stack-initialization-contract.py']}))
 print('Checked integer increment specialization sealed; all-character goal remains incomplete.')
if __name__=='__main__':main()
