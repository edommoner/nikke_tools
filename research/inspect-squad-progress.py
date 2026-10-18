import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ('detail-squad-condition-verification.log','detail-squad-tests.log','detail-squad-api-smoke.log'):
 p=ROOT/'research'/name
 if not p.exists():continue
 b=p.read_bytes();s=b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig',errors='replace');rows=[]
 for line in s.splitlines():
  if line.startswith('{'):
   try:rows.append(json.loads(line))
   except ValueError:pass
 failed=[{k:v for k,v in x.items() if k not in ('cpu_members','gpu_members','source_sha256','observed')} for x in rows if x.get('passed') is False]
 tests=[x[:200] for x in s.splitlines() if re.match(r'test_.*\(test_',x)]
 print(json.dumps(dict(log=name,rows=len(rows),failed=failed[:3],failed_count=len(failed),test_rows=len(tests),last_test=tests[-1] if tests else None,terminal=[x for x in s.splitlines() if re.match(r'Ran \d+ tests|OK$|FAILED|ERROR:|FAIL:',x)]),ensure_ascii=True))
