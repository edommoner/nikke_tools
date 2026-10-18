"""Compile and run CPU-only references before starting the staged GPU suite."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('scaling_fixture_audit',ROOT/'scripts/verify-staged-survival-scaling.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
rows=[]
for name,b,extra in list(v.fixtures())+list(v.real_fixtures()):
    try:
        with v.s.v.context(name,extra):
            compiled=v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True});cpu=v.s.v.v.a.evaluate(b)
        r=dict(name=name,compiled=True,cpu_usable=True,cpu_total=cpu['total_damage'])
    except Exception as exc:r=dict(name=name,compiled=False,cpu_usable=False,error=repr(exc))
    rows.append(r);print(json.dumps(r,ensure_ascii=True),flush=True)
files=['research/audit-survival-scaling-fixtures.py','scripts/verify-staged-survival-scaling.py','scripts/staged-survival-scaling-runtime.py','research/staging/v36/app/detail_gpu.py','research/staging/v36/app/survival_scaling_compat.py','app/survival_compat.py']
r=dict(passed=all(x['compiled'] and x['cpu_usable'] for x in rows),gpu_verified=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-survival-scaling-fixture-audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
