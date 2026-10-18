import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ('detail-random-target-ptx-verification.log','detail-random-target-native-verification.log','detail-random-nested-verification.log','detail-random-tests.log'):
 p=ROOT/'research'/name
 if not p.exists():continue
 b=p.read_bytes();s=b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig',errors='replace');rows=[]
 for line in s.splitlines():
  if line.startswith('{'):
   try:rows.append(json.loads(line))
   except ValueError:pass
 failed=[{k:v for k,v in r.items() if k not in ('cpu_members','gpu_members','observed','source_sha256')} for r in rows if r.get('passed') is False]
 tests=[line[:220] for line in s.splitlines() if re.match(r'test_.*\(test_',line)]
 print(json.dumps(dict(log=name,scenarios=len(rows),failed=failed[:5],failed_count=len(failed),test_rows=len(tests),last_test=tests[-1] if tests else None,terminal=[x for x in s.splitlines() if re.match(r'Ran \d+ tests|OK$|FAILED|ERROR:|FAIL:',x)]),ensure_ascii=True))
