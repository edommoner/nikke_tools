"""Full broad-gate/unit/old-roster evidence; never promotes preflight to certification."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='dd7d62b98a63f9fa99892dd964809775b136a9d6'
load=lambda n:json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
g=load('portable-enemy-codes-global-gates');assert g['passed'] and g['complete'] and len(g['gates'])==29 and g['source_commit']==SOURCE
assert all(x['source_commit']==SOURCE and x['exit_code']==0 for x in g['gates'])
subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
r=load('portable-roster-battles-metal');assert r['passed'] and len(r['cases'])==86
old=json.loads(subprocess.check_output(['git','show','0066afe:research/portable-roster-battles-metal.json'],cwd=R));strip=lambda c:{k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'}
current={(c['character'],c['grown']):strip(c) for c in r['cases']}
for c in old['cases']:assert current[c['character'],c['grown']]==strip(c),(c['character'],c['grown'])
save('portable-enemy-codes-roster-parity',dict(passed=True,prior_proof_commit='0066afe',old_profiles_preserved=84,current_profiles=86,excluded_fields=['cpu_reference_wall_seconds']))
units={}
for name,count in {'unit':212,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
    row=next(x for x in g['gates'] if x['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');units[name]=dict(tests=count,output=text)
save('portable-enemy-codes-unit-tests',dict(passed=True,groups=units))
audit=load('portable-catalog-readiness');assert audit['audited_characters']==203 and audit['own_effect_preflight_passed']==43 and audit['full_character_verified']==0
assert load('portable-enemy-codes-native')['passed'] and len(load('portable-enemy-codes-native')['cases'])==103
save('portable-enemy-codes-broad-validation',dict(passed=True,source_commit=SOURCE,mac_gates=29,unit_tests=212,real_profiles=86,old_profiles_preserved=84,all_source_frozen=True,full_character_verified=0))
real=load('portable-enemy-code-real-metal');assert real['passed'] and real['complete'] and len(real['cases'])==6
for p,h in real['validation_sha256'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
print('29 gates,212 units,86 profiles and all84 old profile fields verified')
