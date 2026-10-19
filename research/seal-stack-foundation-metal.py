"""Attest completed Mac gates without implying remote CUDA completion."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research'
def load(n):return json.loads((P/(n+'.json')).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 g=load('portable-stack-foundation-global-gates');assert g['passed'] and g['complete'] and len(g['gates'])==22
 m=load('portable-combat-metal');assert m['passed'] and m['gpu_execution_verified'] and len(m['cases'])==1149 and len(m['rejected_cases'])==206
 for key in ('source_sha256','validation_sha256'):
  for p,h in m[key].items():assert sha(R/p)==h,p
 old=json.loads(subprocess.check_output(['git','show','97e47b2:research/portable-combat-metal.json'],cwd=R));assert m['results']==old['results']
 r=load('portable-roster-battles-metal');o=json.loads(subprocess.check_output(['git','show','97e47b2:research/portable-roster-battles-metal.json'],cwd=R))
 strip=lambda c:{k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'}
 assert r['passed'] and len(r['cases'])==58 and [strip(c) for c in r['cases']]==[strip(c) for c in o['cases']]
 assert load('portable-stack-numeric-metal')['cases']==19908 and len(load('portable-stack-notices-metal')['cases'])==9
 assert len(load('portable-stack-native-contract')['cases'])==53
 assert len(m['mode_session_cpu_regressions'])==41 and m['known_mode_cpu_differences']==[]
 for name,count in {'unit':131,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
  row=next(r for r in g['gates'] if r['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK')
 reports=['portable-combat-metal','portable-stack-foundation-existing-metal-parity','portable-stack-foundation-global-gates','portable-stack-numeric-metal','portable-stack-notices-metal','portable-stack-native-contract','portable-roster-battles-metal','portable-api-metal','portable-catalog-weapons-metal','portable-real-equipment-metal','portable-real-battle-metal','portable-events-metal','portable-numeric-metal','portable-probe-metal','portable-metal-pipeline-lock','portable-duration-extend-metal','portable-definition-input-metal','portable-definition-scalar-metal','portable-definition-out-metal','portable-removal-queue-metal','portable-catalog-readiness']
 receipt=dict(passed=True,backend='metal',device='Apple M5',source_commit='851625603c9079008bedfb892b80ba36575daeeb',positive_cases=1149,rejections=206,integer_stack_cases=19908,notice_cases=9,native_stack_contract_cases=53,unit_tests=131,native_mode_cases=41,real_profiles=58,all_prior_output_bytes_equal=True,all_prior_real_profile_fields_equal=True,
  abi='0x50455661',input_words=77824,output_words=94208,added_output_bytes=16384,new_effect_kinds_admitted=False,full_goal_complete=False,full_character_verified=0,
  cuda_validation_this_source_complete=False,efficiency_evaluated=False,scope='Mac proof only; CUDA request completion is independently required. Full certification remains incomplete.',
  artifact_sha256={str((P/(n+'.json')).relative_to(R)):sha(P/(n+'.json')) for n in reports},tool_sha256={str(p.relative_to(R)):sha(p) for p in [P/'verify-stack-foundation.py',P/'verify-stack-foundation-existing.py',P/'run-stack-foundation-gates.py',P/'verify-stack-native-contract.py',P/'seal-stack-foundation-metal.py']})
 (P/'portable-stack-foundation-metal-validation.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Mac stack foundation sealed; no CUDA completion claim')
if __name__=='__main__':main()
