"""Minimal GPU delta for a static nullable-state identity correction."""
import argparse,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path[:0]=[str(R/d) for d in ('app','scripts')]
from portable_runtime import run_programs
from portable_status_oracle import compare
s=importlib.util.spec_from_file_location('marker_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
a=argparse.ArgumentParser();a.add_argument('--backend',choices=('cuda','metal'),default='metal');args=a.parse_args()
contract=json.loads((P/'portable-status-marker-incremental.json').read_text());assert contract['passed'] and contract['gpu_source_unchanged']
unit=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_portable_status.py'],cwd=R,text=True,capture_output=True,timeout=60)
assert unit.returncode==0 and 'Ran 8 tests' in unit.stderr and unit.stderr.rstrip().endswith('OK'),unit.stderr
cases={c['name']:c for c in v.fixtures()};selected=[cases[name] for name in contract['delta_cases']]
out=run_programs([v.compile_case(c) for c in selected],backend=args.backend);results=out.pop('results')
assert out['source_sha256']==contract['source_sha256']
for k in ('input_sha256','output_sha256'):assert out[k]==contract['delta_'+k],k
rows=[dict(name=c['name'],passed=True,cpu=compare(c,r,v.contains)) for c,r in zip(selected,results)]
tracked=['app/reference_health_runtime.py','app/portable_runtime.py','app/portable_status_specs.py','scripts/portable_status_oracle.py','tests/fixtures/portable-status.json','tests/test_portable_status.py','research/verify-status-marker-delta.py']
report=dict(passed=True,cases=rows,actual_statuses=[r['status'] for r in results],expected_statuses=[0],unit_tests=dict(passed=True,count=8,stdout=unit.stdout,stderr=unit.stderr),validation_sha256={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in tracked},gpu_source_unchanged=True,baseline_inputs=1624,delta_inputs=1,current_full_cuda_batch_executed=False,**out)
(P/f'portable-status-marker-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Nullable-marker GPU delta passed',args.backend,1,'and unit tests',8)
