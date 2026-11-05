"""Development dispatch; native results are compared only after GPU readback."""
import argparse,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_runtime import run_programs
from portable_status_oracle import compare
s=importlib.util.spec_from_file_location('v',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
p=argparse.ArgumentParser();p.add_argument('--backend',default='metal');args=p.parse_args()
cases=json.loads((R/'tests/fixtures/portable-status.json').read_text())['cases'];programs=[v.compile_case(c) for c in cases]
evidence=run_programs(programs,backend=args.backend);results=evidence.pop('results');rows=[]
for c,r in zip(cases,results):
 try:
  cpu=compare(c,r,v.contains)
  rows.append(dict(name=c['name'],passed=True,cpu=cpu))
 except Exception as error:rows.append(dict(name=c['name'],passed=False,error=str(error),case=c,gpu=r))
(R/f'research/portable-status-operators-{args.backend}.json').write_text(json.dumps(dict(passed=all(r['passed'] for r in rows),cases=rows,**evidence),ensure_ascii=False,indent=2)+'\n');print('Status cases',len(rows),'failures',[(r['name'],r['error'][:600]) for r in rows if not r['passed']]);raise SystemExit(0 if all(r['passed'] for r in rows) else 1)
