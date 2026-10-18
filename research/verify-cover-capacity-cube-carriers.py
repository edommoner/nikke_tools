"""Full raw Moran/A2 skills with Cover cube; no support skill injection."""
import argparse,copy,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('capacity_cube_oracle',ROOT/'scripts/verify-staged-cover-capacity.py');cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap)
hp=cap.load('capacity_cube_HP_fixture','scripts/verify-hp-edge-real.py')
def fixtures():
    _,b,extra=next(x for x in cap.v.real_fixtures() if x[0]=='raw-목단-no-shots');assert not any(extra.values())
    b['profile']['chars']['목단'].update(cube={'name':'렐릭 커버 큐브','level':4},core_enhancement=2,collection_stage='SR15',affinity=20)
    b['stat_deltas']={'목단':{'atk':12000,'hp':100000,'def':250}}
    b['enemy']['patterns']=[dict(id='Moran cover-cube hits',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=40000,target='slot:1',hits=10,interval=1,pierce=True))]
    yield 'raw-Moran-capacity-cover-cube',b,extra
    _,b,extra=next(x for x in hp.fixtures() if x[0]=='raw-A2-mixed-growth');assert not any(extra.values())
    b['profile']['chars']['A2']['cube']={'name':'렐릭 커버 큐브','level':4}
    b['enemy']['patterns'].append(dict(id='A2 cover-cube hits',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=100000,target='all',hits=6,interval=4)))
    yield 'raw-A2-capacity-cover-cube',b,extra
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
    files=['research/verify-cover-capacity-cube-carriers.py','scripts/verify-staged-cover-capacity.py','scripts/staged-cover-capacity-runtime.py','scripts/verify-hp-edge-real.py','scripts/verify-hp-edge.py','scripts/verify-survival-scaling.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','app/detail_world.py','app/detail_boss.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']+['research/staging/v37/app/'+n for n in (['detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json'] if args.backend=='ptx' else ['detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'])]
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};planned=list(fixtures());rows=[];device=cap.v.s.v.v.v.Cuda()
    try:
        for name,b,extra in planned:
            try:r=cap.compare(device,name,b,extra,args.backend)
            except Exception as exc:r=dict(name=name,passed=False,error=repr(exc));print(json.dumps(r),flush=True)
            rows.append(r)
            if not r['passed']:break
    finally:device.close()
    assert hashes=={p:sha(p) for p in files}
    r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(x['passed'] for x in rows),stage_only=True,objective_complete=False,abi=cap.g.DETAIL_ABI,backend=args.backend,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
    (ROOT/args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
