"""Native timeline -> independent comparison after common GPU receipt execution.
CUDA and Metal share authored inputs, the production native-landing packer
and this verifier. Full catalog/variant certification remains incomplete.
"""
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import run_programs
from portable_specs import LIMITS as L,FIELDS as F
from portable_landing_oracle import observe
sp=importlib.util.spec_from_file_location('landing_cases',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
p=argparse.ArgumentParser();p.add_argument('--backend',choices=('metal','cuda'),default='metal');args=p.parse_args()
fixture=ROOT/'tests/fixtures/portable-landings.json';cases=json.loads(fixture.read_text())['cases'];programs=[]
for case in cases:programs.append(v.compile_case(case))
r=run_programs(programs,backend=args.backend);out=ROOT/f'research/portable-landing-prototype-{args.backend}.json';r['passed']=False;out.write_text(json.dumps(r,indent=2)+'\n');rows=[]
for case,gpu in zip(cases,r['results']):
 native=observe(case);v.contains(native['queries'],case['expected_queries'],case['name']+'.hand_native');v.contains(gpu['queries'],native['queries'],case['name']+'.native');v.contains(gpu['queries'],case['expected_queries'],case['name']+'.hand_gpu')
 if 'expected_landing_queue' in case:v.contains(gpu['landing_queue'],case['expected_landing_queue'],case['name']+'.queue')
 if 'expected_pending_burst' in case:v.contains(gpu['pending_burst'],case['expected_pending_burst'],case['name']+'.pending')
 assert gpu['landing_queue']['native']
 rows.append(dict(name=case['name'],passed=True,native=native))
r.update(passed=True,cases=rows,validation_sha256={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [fixture,Path(__file__),ROOT/'scripts/portable_landing_oracle.py',ROOT/'app/reference_health_runtime.py']},scope='Authored actual native timelines and shared GPU packet receipts. Native landing/lifesteal path; full catalog and variant certification incomplete');out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(cases),backend=args.backend,device=r['transport']['device'])))
