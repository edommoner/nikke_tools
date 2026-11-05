"""Seal fixed-source broad gates without promoting mechanics to catalog support."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='ff9a10d175f266708e2d572132b045f1c04083bb';PRIOR='7492276'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
g=load('portable-dispatch-sequence-global-gates');assert g['passed'] and g['complete'] and len(g['gates'])==31 and g['source_commit']==SOURCE
assert all(x['source_commit']==SOURCE and x['exit_code']==0 for x in g['gates'])
subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True,stdout=subprocess.DEVNULL)
old=lambda n:json.loads(subprocess.check_output(['git','show',PRIOR+':research/'+n+'.json'],cwd=R))
m=load('portable-combat-metal');previous=old('portable-combat-metal')
for key in ['source_sha256','input_sha256','output_sha256','actual_statuses','expected_statuses','batch_layout','rejected_cases']+[k for k in previous if k.endswith('_cpu_regressions') or k.startswith('known_')]:assert m[key]==previous[key],key
assert m['passed'] and len(m['cases'])==1692 and len(m['rejected_cases'])==314
r=load('portable-roster-battles-metal');assert r['passed'] and len(r['cases'])==86
old_roster=old('portable-roster-battles-metal')
# Only the measured wall time may differ; all other fields must match.
current={(c['character'],c['grown']):c for c in r['cases']}
for c in old_roster['cases']:
    now=current[c['character'],c['grown']]
    differences=[k for k in set(c)|set(now) if c.get(k)!=now.get(k)]
    assert all(k=='cpu_reference_wall_seconds' for k in differences),(c['character'],c['grown'],differences)
units={}
for name,count in {'unit':220,'staged-native':9,'source-native':6,'native-mode-spec':4,'native-mode-input':3,'reference-rewrite':3}.items():
 row=next(x for x in g['gates'] if x['name']==name);text=Path(row['log']).read_text();assert f'Ran {count} tests' in text and text.rstrip().endswith('OK');units[name]=dict(tests=count,output=text)
s=load('portable-dispatch-sequence-metal');assert s['passed'] and s['source_commit']==SOURCE and s['programs']==2050 and s['dispatch_counts']==[1024,1024,2]
assert s['prefix_output_sha256']==m['output_sha256'] and s['previous_input_sha256']==m['input_sha256']
for p,h in s['validation_sha256'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
assert load('portable-api-metal')['passed'];audit=load('portable-catalog-readiness');assert audit['own_effect_preflight_passed']==43 and audit['full_character_verified']==0
save('portable-dispatch-sequence-broad-validation',dict(passed=True,source_commit=SOURCE,mac_gates=31,unit_tests=220,real_profiles=86,old_profiles_preserved=86,previous_core_inputs_preserved=2006,sequence_inputs=2050,all_source_frozen=True,unit_groups=units,full_character_verified=0))
print('31 gates,220 units,86 old real profiles and all2006 core readbacks verified')
