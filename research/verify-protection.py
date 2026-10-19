import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_runtime import run_programs,PortableExecutionError
from portable_protection_oracle import compare,observe
s=importlib.util.spec_from_file_location('common',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
a=argparse.ArgumentParser();a.add_argument('--backend',default='metal');a.add_argument('--native-only',action='store_true');args=a.parse_args()
tracked=['app/portable_protection_specs.py','app/protection_runtime.py','app/reference_health_runtime.py','app/portable_runtime.py','scripts/portable_protection_oracle.py','tests/fixtures/portable-protection.json','research/verify-protection.py']
hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in tracked}
cases=json.loads((R/'tests/fixtures/portable-protection.json').read_text())['cases'];rows=[]
if args.native_only:
 for case in cases:rows.append(dict(name=case['name'],passed=True,cpu=observe(case)))
 evidence={}
else:
 try:
  output=run_programs([v.compile_case(c) for c in cases],backend=args.backend);results=output.pop('results');evidence=output
 except PortableExecutionError as error:results=error.results;evidence=error.evidence
 for c,r in zip(cases,results):
  try:
   assert r['status']==0,('GPU status',r['status'])
   rows.append(dict(name=c['name'],passed=True,cpu=compare(c,r,v.contains)))
  except Exception as error:rows.append(dict(name=c['name'],passed=False,error=str(error),gpu=r,case=c))
assert hashes=={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in tracked}
report=dict(validation_sha256=hashes,passed=all(r['passed'] for r in rows),cases=rows,**evidence);name='native' if args.native_only else args.backend
(R/f'research/portable-protection-{name}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Protection',len(rows),'failures',[(r['name'],r.get('error','')[:300]) for r in rows if not r['passed']]);raise SystemExit(0 if report['passed'] else 1)
