import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ['detail-cleanse-verification.log','detail-cleanse-nested-verification.log','detail-cleanse-focused-tests.log','detail-cleanse-tests.log']:
 p=ROOT/'research'/name
 if not p.exists():continue
 b=p.read_bytes();s=b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
 rows=[json.loads(line) for line in s.splitlines() if line.startswith('{') and line.endswith('}')]
 out={'log':name,'scenario_rows':len(rows),'passed':sum(r.get('passed') is True for r in rows),'failed':[{'name':r.get('name'), 'checks':r.get('checks')} for r in rows if r.get('passed') is False]}
 tests=[line for line in s.splitlines() if line.startswith('test_')]
 if tests:out['test_rows']=len(tests);out['last_test']=tests[-1][:150]
 out['terminal_lines']=[line for line in s.splitlines() if line.startswith(('Ran ','OK','FAILED','FAIL:','ERROR:'))]
 if 'Traceback' in s:out['traceback_tail']=s[-700:]
 print(json.dumps(out,ensure_ascii=True))
