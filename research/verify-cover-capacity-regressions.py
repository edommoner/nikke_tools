"""Focused v37 regression of previous cover/heal/HP/down lifecycles."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
cap=load('capacity_legacy_loader','scripts/verify-staged-cover-capacity.py');old=cap.v;surv=old.s;hp=load('capacity_HP_oracle','scripts/verify-hp-edge.py')
def fixtures():
    planned=[(old,*x) for x in old.fixtures()]+[(old,*x) for x in old.real_fixtures() if x[0].endswith(('-incoming','-revival'))]+[(hp,*x) for x in hp.fixtures()]+[(surv,*x) for x in surv.fixtures(quick=True)]
    planned += [(surv.v,*x) for x in surv.v.fixtures() if x[0].startswith(('cover-','lowest-cover-'))]
    assert len(planned)==74,len(planned)
    return planned
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
    planned=fixtures()
    files=['research/verify-cover-capacity-regressions.py','scripts/verify-staged-cover-capacity.py','scripts/staged-cover-capacity-runtime.py','scripts/verify-hp-edge.py','scripts/verify-survival-scaling.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','app/detail_world.py','app/detail_boss.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']+['research/staging/v37/app/'+n for n in (['detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json'] if args.backend=='ptx' else ['detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'])]
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};rows=[];device=old.s.v.v.v.Cuda()
    try:
        for m,name,b,extra in planned:
            try:r=m.compare(device,name,b,extra,args.backend)
            except Exception as exc:r=dict(name=name,passed=False,error=repr(exc));print(json.dumps(r),flush=True)
            rows.append(r)
            if not r['passed']:break
    finally:device.close()
    assert hashes=={p:sha(p) for p in files}
    r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(x['passed'] for x in rows),stage_only=True,objective_complete=False,abi=cap.g.DETAIL_ABI,backend=args.backend,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
    (ROOT/args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
