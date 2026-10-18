"""Exact historical v41 CPU squad totals under the new charge extension."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('charge_verifier',ROOT/'research/verify-heal-charge.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
archive=ROOT/'research/ports/v41-final/research/ports/v41-heal-sharing-staged-verified/research'
reports=[archive/('detail-heal-sharing-'+group+'-native.json') for group in ('new','legacy')]
expected={r['name']:r['cpu_total'] for p in reports for r in json.loads(p.read_text(encoding='utf-8'))['cases']}
planned=d.fixtures('legacy');assert len(planned)==len(expected)==178
paths=reports+[ROOT/p for p in ['research/probe-heal-charge-cpu-legacy.py','research/verify-heal-charge.py','research/heal-charge-fixtures.py','research/staging/v42/app/heal_charge_compat.py','research/staging/v42/app/detail_gpu.py']]+list((ROOT/'scripts').glob('*.py'))+list((ROOT/'app').glob('*.py'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={p.relative_to(ROOT).as_posix():sha(p) for p in paths};rows=[]
for oracle,name,b,x in planned:
    with d.v.s.v.context(name,x):result=d.v.s.v.v.a.evaluate(b)
    actual=result['total_damage'];r=dict(name=name,passed=actual==expected[name],expected_v41=expected[name],actual_v42=actual);rows.append(r)
    if not r['passed']:print(json.dumps(r,ensure_ascii=True),flush=True)
assert hashes=={p:sha(ROOT/p) for p in hashes}
report=dict(passed=all(r['passed'] for r in rows),stage_only=True,gpu_run=False,cpu_model_extended=True,in_game_rules_verified=False,objective_complete=False,comparison_scope='Exact historical whole-squad total only, not historical per-member/frame parity.',cases=rows,source_sha256=hashes)
(ROOT/'research/detail-heal-charge-cpu-legacy.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=report['passed'],cases=len(rows))));raise SystemExit(0 if report['passed'] else 1)
