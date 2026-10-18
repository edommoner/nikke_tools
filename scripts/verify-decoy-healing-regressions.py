"""Focused v38 regressions for existing layers, HP/cover, and down/revive."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
d=load('decoy_regression_loader','scripts/verify-decoy-healing.py');old=d.v;surv=old.s;incoming=surv.v;cap=load('decoy_cover_capacity_oracle','scripts/verify-cover-capacity.py')
def fixtures():
    planned=[(old,*x) for x in old.fixtures()]+[(surv,*x) for x in surv.fixtures(quick=True)]+[(cap,*x) for x in cap.fixtures()]+[(cap,*x) for x in cap.real_fixtures() if x[0]=='raw-Tia-capacity-owned-cover-cube']
    planned += [(incoming,*x) for x in incoming.fixtures() if x[0].startswith('layers-') or x[0]=='decoy-consumed-state-end']
    assert len(planned)>=60,len(planned);return planned
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--output',required=True);args=ap.parse_args();planned=fixtures()
    files=['scripts/verify-decoy-healing-regressions.py','scripts/verify-decoy-healing.py','scripts/verify-cover-capacity.py','scripts/verify-survival-scaling.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','scripts/audit-incoming-damage.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','app/detail_world.py','app/detail_boss.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']+['app/'+n for n in (['detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json'] if args.backend=='ptx' else ['detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'])]
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};rows=[];device=old.s.v.v.v.Cuda()
    try:
        for oracle,name,b,extra in planned:
            try:r=oracle.compare(device,name,b,extra,args.backend)
            except Exception as exc:r=dict(name=name,passed=False,error=repr(exc));print(json.dumps(r),flush=True)
            rows.append(r)
            if not r['passed']:break
    finally:device.close()
    assert hashes=={p:sha(p) for p in files}
    r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(x['passed'] for x in rows),stage_only=False,objective_complete=False,abi=d.g.DETAIL_ABI,backend=args.backend,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
    (ROOT/args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
