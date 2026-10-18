"""Compare all 153 v40 CPU totals against sealed evidence, without a GPU."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('sharing_verifier',ROOT/'research/verify-heal-sharing.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
archive=ROOT/'research/ports/v40-final/research/ports/v40-healing-storage-staged-verified/research'
names=['detail-healing-storage-'+group+'-native.json' for group in ['authored','real','extra','regression']]
previous=[r for p in names for r in json.loads((archive/p).read_text(encoding='utf-8'))['cases']]
expected={r['name']:r['cpu_total'] for r in previous};planned=d.fixtures('legacy');assert len(planned)==len(expected)==153
files=['research/probe-heal-sharing-cpu-legacy.py','research/verify-heal-sharing.py','research/heal-sharing-fixtures.py','research/staging/v41/app/heal_sharing_compat.py','scripts/staged-heal-sharing-runtime.py','app/healing_storage_compat.py','app/outgoing_healing_compat.py','app/engine_compat.py']
paths=[ROOT/p for p in files]+[archive/p for p in names]+list((ROOT/'scripts').glob('*.py'))+list((ROOT/'app').glob('*.py'))+[ROOT/'research/staging/v41/app/detail_gpu.py']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={p.relative_to(ROOT).as_posix():sha(p) for p in paths};rows=[]
for oracle,name,b,x in planned:
    with d.v.s.v.context(name,x):result=d.v.s.v.v.a.evaluate(b)
    actual=result['total_damage'];row=dict(name=name,passed=actual==expected[name],expected_v40=expected[name],actual_v41=actual);rows.append(row)
    if not row['passed']:print(json.dumps(row,ensure_ascii=True),flush=True)
assert hashes=={p:sha(ROOT/p) for p in hashes}
report=dict(passed=all(r['passed'] for r in rows),stage_only=True,gpu_run=False,objective_complete=False,comparison_scope='Exact historical whole-squad totals only; no historical per-member/frame equality claim.',cases=rows,source_sha256=hashes)
(ROOT/'research/detail-heal-sharing-cpu-legacy.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=report['passed'],cases=len(rows))));raise SystemExit(0 if report['passed'] else 1)
