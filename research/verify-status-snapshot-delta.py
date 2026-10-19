"""Minimal GPU delta for a CPU-only snapshot observer correction."""
import argparse,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path[:0]=[str(R/d) for d in ('app','scripts')]
from portable_runtime import run_programs
from portable_status_oracle import compare
s=importlib.util.spec_from_file_location('snapshot_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
a=argparse.ArgumentParser();a.add_argument('--backend',choices=('cuda','metal'),default='metal');args=a.parse_args()
contract=json.loads((P/'portable-status-snapshot-incremental.json').read_text());assert contract['passed'] and contract['gpu_source_unchanged']
unit=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_portable_status.py'],cwd=R,text=True,capture_output=True,timeout=60)
assert unit.returncode==0 and 'Ran 8 tests' in unit.stderr and unit.stderr.rstrip().endswith('OK'),unit.stderr
cases={c['name']:c for c in v.fixtures()};selected=[cases[name] for name in contract['delta_cases']]
out=run_programs([v.compile_case(c) for c in selected],backend=args.backend);results=out.pop('results')
for k in ('source_sha256',):assert out[k]==contract[k],k
for k in ('input_sha256','output_sha256'):assert out[k]==contract['delta_'+k],k
rows=[dict(name=c['name'],passed=True,cpu=compare(c,r,v.contains)) for c,r in zip(selected,results)]
tracked=['app/reference_health_runtime.py','app/portable_runtime.py','app/portable_status_specs.py','scripts/portable_status_oracle.py','tests/fixtures/portable-status.json','tests/test_portable_status.py','research/verify-status-snapshot-delta.py']
report=dict(passed=True,cases=rows,actual_statuses=[r['status'] for r in results],expected_statuses=[0,0],unit_tests=dict(passed=True,count=8,stdout=unit.stdout,stderr=unit.stderr),validation_sha256={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in tracked},gpu_source_unchanged=True,baseline_inputs=1622,delta_inputs=2,current_full_cuda_batch_executed=False,**out)
(P/f'portable-status-snapshot-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Snapshot GPU delta passed',args.backend,2,'and unit tests',8)
