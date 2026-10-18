"""Resume only the unfinished API/PTX stages after verified long battles."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for path,count in [('research/detail-incoming-native-verification.json',80),('research/detail-incoming-long-verification.json',4)]:
 r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'] and len(r['cases'])==count and r['not_run_cases']==0
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in r['source_sha256'].items())
old=ROOT/'research/detail-incoming-api-verification.log';archive=ROOT/'research/detail-incoming-api-sandbox-failure.log'
if not archive.exists():
 raw=old.read_bytes();assert b'EACCES' in raw;archive.write_bytes(raw)
steps=[(['node','scripts/smoke-detail-incoming.mjs','research/detail-incoming-api-fixture.json'],'research/detail-incoming-api-verification.log'),([sys.executable,'scripts/verify-incoming-detail.py','--backend','ptx','--fail-fast','--output','research/detail-incoming-ptx-verification.json'],'research/detail-incoming-ptx-verification.log')]
for command,log in steps:
 print('Running '+command[1],flush=True)
 with (ROOT/log).open('w',encoding='utf-8') as output:result=subprocess.run(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
 if result.returncode:raise SystemExit(result.returncode)
 print('Passed '+command[1],flush=True)
