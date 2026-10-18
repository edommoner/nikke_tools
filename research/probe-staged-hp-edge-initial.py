"""Initial native damage/frame proof before adding explicit notification logs."""
import importlib.util,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hp_probe',ROOT/'scripts/verify-staged-hp-edge.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
files=['research/probe-staged-hp-edge-initial.py','scripts/verify-staged-hp-edge.py','scripts/verify-survival-detail.py','scripts/staged-hp-edge-runtime.py','app/survival_compat.py']+['research/staging/v35/app/'+n for n in ('detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json')]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};rows=[];device=v.s.v.v.v.Cuda()
try:
    for name,b,extra in v.fixtures():
        b.pop('_debug_hp_events')
        try:r=v.s.compare(device,name,b,extra,'native')
        except Exception as exc:r=dict(name=name,passed=False,error=repr(exc));print(json.dumps(r),flush=True)
        rows.append(r)
        if not r['passed']:break
finally:device.close()
assert hashes=={p:sha(p) for p in files}
report=dict(passed=len(rows)==8 and all(r['passed'] for r in rows),stage_only=True,objective_complete=False,hp_notification_order_verified=False,cases=rows,source_sha256=hashes)
(ROOT/'research/detail-hp-edge-initial-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
