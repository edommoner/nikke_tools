"""Compare extended CPU against immutable v39 totals before GPU regressions.

Historical values are expected test results only, never GPU input data.
"""
import hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('storage_cpu_legacy_definitions',ROOT/'research/verify-healing-storage-regressions.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
archive='research/ports/v39-outgoing-healing-staged-verified';reports=[archive+'/research/detail-outgoing-healing-'+k+'-native.json' for k in ('authored','real','regression')]
expected=[]
for f in reports:
    r=json.loads((ROOT/f).read_text(encoding='utf-8'));assert r['passed'];expected+=r['cases']
planned=d.fixtures();assert len(expected)==len(planned)==124;rows=[]
files=['research/verify-healing-storage-cpu-legacy.py','research/verify-healing-storage-regressions.py','scripts/staged-healing-storage-runtime.py','scripts/verify-outgoing-healing.py','scripts/verify-outgoing-healing-regressions.py','scripts/verify-decoy-healing.py','scripts/verify-decoy-healing-regressions.py','scripts/verify-cover-capacity.py','scripts/verify-survival-scaling.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','research/staging/v40/app/healing_storage_compat.py','app/engine_worker.py','app/engine_compat.py','app/outgoing_healing_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']+reports
sha=lambda f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest();hashes={f:sha(f) for f in files}
for (oracle,name,b,x),previous in zip(planned,expected):
    assert name==previous['name'],(name,previous['name'])
    try:
        with d.out.v.s.v.context(name,x):result=d.out.v.s.v.v.a.evaluate(b)
        actual=result['total_damage'];row=dict(name=name,passed=actual==previous['cpu_total'],expected_v39=previous['cpu_total'],actual_v40=actual)
    except Exception as e:row=dict(name=name,passed=False,error=repr(e))
    rows.append(row)
    if not row['passed']:print(json.dumps(row,ensure_ascii=True),flush=True)
assert hashes=={f:sha(f) for f in files}
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==124 and all(x['passed'] for x in rows),cases=rows,gpu_run=False,cpu_model_extended=True,comparison_scope='Exact whole-squad total against sealed v39 CPU results; not per-member/event-state parity.',objective_complete=False,source_sha256=hashes)
(ROOT/'research/detail-healing-storage-cpu-legacy.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=r['passed'],cases=len(rows),gpu_run=False)),flush=True);raise SystemExit(0 if r['passed'] else 1)
