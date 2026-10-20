import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_runtime import run_programs,PortableExecutionError
from portable_code_oracle import compare,observe
s=importlib.util.spec_from_file_location('main_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
a=argparse.ArgumentParser();a.add_argument('--backend',default='metal');a.add_argument('--native-only',action='store_true');args=a.parse_args()
tracked=['gpu/event_runtime.slang','gpu/admission_runtime.slang','app/portable_specs.py','app/portable_code_specs.py','app/portable_trigger_specs.py','app/portable_runtime.py','app/portable_recipient_specs.py','app/portable_specs.py','scripts/portable_code_oracle.py','tests/fixtures/portable-enemy-codes.json','research/verify-codes.py'];hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in tracked}
cases=json.loads((R/'tests/fixtures/portable-enemy-codes.json').read_text())['cases'];rows=[];evidence={}
if args.native_only:
 for c in cases:rows.append(dict(name=c['name'],passed=True,native=observe(c)))
else:
 try:output=run_programs([v.compile_case(c) for c in cases],backend=args.backend);results=output.pop('results');evidence=output
 except PortableExecutionError as error:results=error.results;evidence=error.evidence
 for c,r in zip(cases,results):
  try:
   assert r['status']==0,('GPU status',r['status']);native=compare(c,r,v.contains);rows.append(dict(name=c['name'],passed=True,native=native))
  except Exception as error:rows.append(dict(name=c['name'],passed=False,error=str(error),case=c,gpu=r))
assert hashes=={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in tracked}
report=dict(passed=all(c['passed'] for c in rows),cases=rows,validation_sha256=hashes,**evidence);suffix='native' if args.native_only else args.backend
(R/f'research/portable-enemy-codes-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Enemy codes',len(rows),'failures',[(r['name'],r.get('error','')[:300]) for r in rows if not r['passed']]);raise SystemExit(0 if report['passed'] else 1)
