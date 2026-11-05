"""Keep every decoded field and native comparison, excluding CPU wall time only."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research'
load=lambda n:json.loads((P/(n+'.json')).read_text())
r=load('portable-roster-battles-metal');assert r['passed'] and len(r['cases'])==64
prior=json.loads(subprocess.check_output(['git','show','3f661c8:research/portable-roster-battles-metal.json'],cwd=R))
strip=lambda c:{k:v for k,v in c.items() if k!='cpu_reference_wall_seconds'}
current={(c['character'],c['grown']):strip(c) for c in r['cases']}
for c in prior['cases']:assert current[c['character'],c['grown']]==strip(c)
frozen=load('portable-status-before-marker-roster')
for c in frozen['cases']:
 value=current[c['character'],c['grown']];h=hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert h==c['sha256']
x=dict(passed=True,current_profiles=64,previous_stage_profiles_preserved=len(prior['cases']),before_nullable_fix_profiles_preserved=len(frozen['cases']),excluded_fields=['cpu_reference_wall_seconds'],all_other_decoded_fields_and_cpu_reference_preserved=True)
(P/'portable-status-roster-parity.json').write_text(json.dumps(x,indent=2)+'\n');print('All roster fields preserved')
