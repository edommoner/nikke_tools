"""Independent cover cases on the frozen candidate while lost-HP HP-gain is fixed."""
import hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('cover_scaling_probe',ROOT/'scripts/verify-staged-survival-scaling.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
files=['research/verify-survival-scaling-cover-only.py','scripts/verify-staged-survival-scaling.py','scripts/staged-survival-scaling-runtime.py','app/survival_compat.py','app/engine_worker.py','app/engine_compat.py']+['research/staging/v36/app/'+n for n in ('detail_gpu.py','survival_scaling_compat.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json')]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};planned=[x for x in v.fixtures() if x[0].startswith('cover-')];rows=[];device=v.s.v.v.v.Cuda()
try:
    for name,b,extra in planned:
        try:r=v.compare(device,name,b,extra,'native')
        except Exception as exc:r=dict(name=name,passed=False,error=repr(exc));print(json.dumps(r),flush=True)
        rows.append(r)
finally:device.close()
assert hashes=={p:sha(p) for p in files}
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(x['passed'] for x in rows),stage_only=True,objective_complete=False,planned_cases=len(planned),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
(ROOT/'research/detail-survival-scaling-cover-native-probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
