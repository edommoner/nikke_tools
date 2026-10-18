"""Reuse one CUDA context and one PTX JIT for all full battle groups."""
import argparse,hashlib,importlib.util,json
from contextlib import redirect_stdout
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('warm_survival_oracle',ROOT/'scripts/verify-staged-survival.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);args=ap.parse_args()
files=list(json.loads((ROOT/'research/detail-staged-survival-initial-quick.json').read_text(encoding='utf-8'))['source_sha256'])+['research/verify-staged-survival-warm-suite.py']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files}
device=m.v.v.v.Cuda()
try:
    for label,planned in [('full',list(m.fixtures())),('regression',list(m.v.fixtures(False))),('long',list(m.v.long_fixtures()))]:
        print('Running '+args.backend+' '+label,flush=True);rows=[]
        path=ROOT/f'research/detail-staged-survival-{args.backend}-{label}.json'
        with path.with_suffix('.log').open('w',encoding='utf-8') as log,redirect_stdout(log):
            for name,b,extra in planned:
                try:row=m.compare(device,name,b,extra,args.backend)
                except Exception as error:row=dict(name=name,passed=False,error=repr(error));print(json.dumps(row),flush=True)
                rows.append(row)
                if not row['passed']:break
        assert hashes=={p:sha(p) for p in files}
        passed=len(rows)==len(planned) and all(r['passed'] for r in rows)
        report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=passed,objective_complete=False,abi=m.g.DETAIL_ABI,stage_only=True,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if not passed:raise SystemExit(1)
        print('Passed '+args.backend+' '+label+' '+str(len(rows)),flush=True)
finally:device.close()
