"""Verify current gates; preserve the initial unlocalized mismatch separately."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='14c8e2e61fd6eeb9950a13c76f217ae62ca82fd9';PRIOR='ce01fad'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
g=load('portable-element-captured-global-gates');assert g['passed'] and g['complete'] and len(g['gates'])==31 and g['source_commit']==SOURCE
assert all(x['exit_code']==0 and x['source_commit']==SOURCE for x in g['gates'])
subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
m=load('portable-combat-metal');assert m['passed'] and len(m['cases'])==1848 and len(m['rejected_cases'])==334 and len(m['element_override_cpu_regressions'])==156
assert m['element_override_existing_parity']['passed'] and m['element_override_existing_parity']['prior_inputs']==2006
old=json.loads(subprocess.check_output(['git','show',PRIOR+':research/portable-roster-battles-metal.json'],cwd=R));r=load('portable-roster-battles-metal');assert r['passed'] and len(r['cases'])==86
lookup={(c['character'],c['grown']):c for c in r['cases']}
for c in old['cases']:
 now=lookup[c['character'],c['grown']];changed=[k for k in set(c)|set(now) if c.get(k)!=now.get(k)]
 assert all(k=='cpu_reference_wall_seconds' for k in changed),(c['character'],c['grown'],changed)
units={}
for name,count in {'unit':237,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
 row=next(x for x in g['gates'] if x['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');units[name]=dict(tests=count,output=text)
a=load('portable-api-metal');assert a['passed'] and len(a['element_override_execution'])==9
assert load('portable-element-overrides-native')['passed'] and len(load('portable-element-overrides-native')['cases'])==156
readback=load('portable-element-core-readback-receipt');assert readback['passed'] and not readback['changed'] and readback['no_gpu_retry'] and readback['no_output_normalization']
assert readback['evidence']['input_sha256']==m['input_sha256'] and readback['evidence']['output_sha256']==m['output_sha256']
for path,key in [('research/verify-element-regression.py','original_driver_sha256'),('research/capture-element-regression.py','capture_tool_sha256')]:assert hashlib.sha256((R/path).read_bytes()).hexdigest()==readback[key]
initial=load('portable-element-initial-core-finding');assert initial['open_finding'] and initial['failed_readback_was_not_retained'] and not initial['passed']
repro=load('portable-element-reproduction');transfer=load('portable-element-transfer-completed');assert repro['passed'] and repro['complete'] and len(repro['runs'])==4
assert all(x['old_output_matches_prior'] and x['evidence']['output_sha256']==transfer['full_output_sha256'] for x in repro['runs'])
audit=load('portable-catalog-readiness');assert audit['own_effect_preflight_passed']==43 and audit['full_character_verified']==0 and sum(audit['issues'].values())==384
save('portable-element-broad-validation',dict(passed=True,all_current_gates_passed=True,source_commit=SOURCE,mac_gates=31,unit_tests=237,real_profiles=86,old_profiles_preserved=86,core_programs=2182,prior_core_inputs_preserved=2006,element_native_cases=156,element_api_cases=9,unit_groups=units,all_compute_sources_frozen=True,initial_metal_finding_open=True,initial_metal_finding='portable-element-initial-core-finding.json',scope='Current required gates pass; first unretained raw mismatch is unlocalized and remains documented, not claimed fixed.',full_character_verified=0,full_goal_complete=False))
print('Current31 gates,237 units,86 old profiles and all2182 inputs verified;initial mismatch remains documented')
