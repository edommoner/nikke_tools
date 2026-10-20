"""Full broad-gate/unit/old-roster evidence; never promotes preflight to certification."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='ed68e6847fe8e7f0d13ed81a6af6dec6837ca915'
load=lambda n:json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
g=load('portable-named-states-global-gates');assert g['passed'] and g['complete'] and len(g['gates'])==27 and g['source_commit']==SOURCE
assert all(x['source_commit']==SOURCE and x['exit_code']==0 for x in g['gates'])
subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
r=load('portable-roster-battles-metal');assert r['passed'] and len(r['cases'])==84
old=json.loads(subprocess.check_output(['git','show','e4ea13c:research/portable-roster-battles-metal.json'],cwd=R));strip=lambda c:{k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'}
current={(c['character'],c['grown']):strip(c) for c in r['cases']}
for c in old['cases']:assert current[c['character'],c['grown']]==strip(c),(c['character'],c['grown'])
save('portable-named-states-roster-parity',dict(passed=True,prior_proof_commit='e4ea13c',old_profiles_preserved=82,current_profiles=84,excluded_fields=['cpu_reference_wall_seconds']))
units={}
for name,count in {'unit':195,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
    row=next(x for x in g['gates'] if x['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');units[name]=dict(tests=count,output=text)
save('portable-named-states-unit-tests',dict(passed=True,groups=units))
audit=load('portable-catalog-readiness');assert audit['audited_characters']==203 and audit['own_effect_preflight_passed']==42 and audit['full_character_verified']==0
assert load('portable-named-states-native')['passed'] and len(load('portable-named-states-native')['cases'])==65
save('portable-named-states-broad-validation',dict(passed=True,source_commit=SOURCE,mac_gates=27,unit_tests=195,real_profiles=84,old_profiles_preserved=82,all_source_frozen=True,full_character_verified=0))
print('27 gates,195 units,84 profiles and all82 old profile fields verified')
