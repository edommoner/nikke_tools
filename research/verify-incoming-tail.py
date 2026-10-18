"""One GPU worker at a time; run alongside at most one normal-test worker."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'research/detail-incoming-native-verification.json').read_text(encoding='utf-8'))
assert r['passed'] and len(r['cases'])==80 and r['not_run_cases']==0
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in r['source_sha256'].items())
steps=[
 ([sys.executable,'scripts/verify-incoming-detail.py','--long','--fail-fast','--output','research/detail-incoming-long-verification.json'],'research/detail-incoming-long-verification.log'),
 (['node','scripts/smoke-detail-incoming.mjs','research/detail-incoming-api-fixture.json'],'research/detail-incoming-api-verification.log'),
 ([sys.executable,'scripts/verify-incoming-detail.py','--backend','ptx','--fail-fast','--output','research/detail-incoming-ptx-verification.json'],'research/detail-incoming-ptx-verification.log')]
for command,log in steps:
 print('Running '+command[1]+' '+('long' if '--long' in command else 'PTX' if 'ptx' in command else 'API'),flush=True)
 with (ROOT/log).open('w',encoding='utf-8') as output:result=subprocess.run(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
 if result.returncode:raise SystemExit(result.returncode)
 print('Passed '+command[1],flush=True)
