"""Development dispatch for the same raw stack cases on either GPU backend."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts')]
from portable_runtime import run_programs
from portable_stack_oracle import compare
s=importlib.util.spec_from_file_location('stack_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
p=argparse.ArgumentParser();p.add_argument('--backend',default='metal');args=p.parse_args()
cases=json.loads((R/'tests/fixtures/portable-stacks.json').read_text())['cases'];programs=[v.compile_case(c) for c in cases]
evidence=run_programs(programs,backend=args.backend);results=evidence.pop('results');rows=[]
for c,r in zip(cases,results):
    try:
        cpu=compare(c,r,v.contains)
        v.contains(r['queries'],c.get('expected_queries',[]),c['name']+'.authored')
        if 'expected_final' in c:v.contains(r,c['expected_final'],c['name']+'.authored-final')
    except Exception as error:
        rows.append(dict(name=c['name'],passed=False,error=str(error),case=c,gpu=r));continue
    rows.append(dict(name=c['name'],passed=True,cpu=cpu))
(R/f'research/portable-stack-operators-{args.backend}.json').write_text(json.dumps(dict(passed=all(r['passed'] for r in rows),cases=rows,**evidence),ensure_ascii=False,indent=2)+'\n');print('Stack operator cases',len(rows),'failures',[(r['name'],r['error'][:500]) for r in rows if not r['passed']],args.backend);raise SystemExit(0 if all(r['passed'] for r in rows) else 1)
