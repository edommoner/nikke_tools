"""Run existing HP/down/revive oracles against staged v36 PTX, source bound."""
import hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
g=load('scaling_legacy_runtime','scripts/staged-survival-scaling-runtime.py').install()
modules=[load('scaling_legacy_'+str(i),'scripts/'+path) for i,path in enumerate(['verify-hp-edge.py','verify-hp-edge-real.py','verify-hp-edge-namespace.py','verify-survival-detail.py'])]
files=['research/verify-survival-scaling-legacy.py','scripts/staged-survival-scaling-runtime.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','scripts/verify-incoming-detail.py']+['scripts/'+path for path in ['verify-hp-edge.py','verify-hp-edge-real.py','verify-hp-edge-namespace.py','verify-survival-detail.py']]+['research/staging/v36/app/'+n for n in ['detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json','survival_scaling_compat.py']]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};rows=[];planned=[(m,name,b,extra) for m in modules for name,b,extra in m.fixtures()];device=modules[0].s.v.v.v.Cuda()
try:
    for m,name,b,extra in planned:
        try:r=m.compare(device,name,b,extra,'ptx')
        except Exception as exc:r=dict(name=name,passed=False,error=repr(exc));print(json.dumps(r),flush=True)
        rows.append(r)
        if not r['passed']:break
finally:device.close()
assert hashes=={p:sha(p) for p in files}
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(x['passed'] for x in rows),stage_only=True,objective_complete=False,abi=g.DETAIL_ABI,backend='ptx',planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
(ROOT/'research/detail-survival-scaling-legacy-ptx.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
