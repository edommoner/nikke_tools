"""Native duration/independent enemy-resident proof after actual GPU readback."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_runtime import run_programs
sp=importlib.util.spec_from_file_location('duration_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
from portable_removal_oracle import observe
p=argparse.ArgumentParser();p.add_argument('--backend',choices=('metal','cuda'),default='metal');args=p.parse_args()
cases=json.loads((R/'tests/fixtures/portable-duration-extend.json').read_text())['cases'];programs=[v.compile_case(c) for c in cases]
result=run_programs(programs,backend=args.backend);path=R/f'research/portable-duration-extend-{args.backend}.json'
result.update(passed=False,stage='readback-before-native-comparison',cpu_trace_used_as_gpu_input=False)
path.write_text(json.dumps(result,indent=2)+'\n')
from portable_duration_extend_oracle import compare
rows=[]
for case,gpu in zip(cases,result['results']):
 v.contains(gpu['queries'],case['expected_queries'],case['name']+'.hand')
 cpu=compare(case,gpu,v.contains)
 rows.append(dict(name=case['name'],passed=True,native=cpu))
result.update(passed=True,stage='native-verified',cases=rows)
path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('Native duration extension GPU cases passed',len(rows),args.backend,flush=True)
