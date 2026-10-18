"""Actual Moran/Biscuit squads, including post-revival hits and owned gear."""
import argparse,copy,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('scaling_actual_oracle',ROOT/'scripts/verify-staged-survival-scaling.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
def fixtures():
    base=list(v.real_fixtures())
    for name,b,extra in base:
        if name.endswith('-revival'):b['enemy']['patterns'].append(dict(id='after revival',kind='attack',delay=4,until={'time':10},spec=dict(coeff=100,atk=800000,target='slot:4',hits=10,interval=.5,pierce=True)))
        yield name,b,extra
    for character in ('목단','비스킷'):
        original=next(x for x in base if x[0]=='raw-'+character+'-incoming')
        for variant in ('owned-growth','reordered'):
            name,b,extra=copy.deepcopy(original);name+='-'+variant
            if variant=='reordered':
                b['squad']=list(reversed(b['squad']))
                for p in b['enemy']['patterns']:
                    if p['spec']['target']=='slot:1':p['spec']['target']='slot:5'
            else:
                c=b['profile']['chars'][character];c.update(breakthrough=3,core_enhancement=2,affinity=20,skill_levels={'1':7,'2':5,'3':9},collection_stage='SR15',cube={'name':'렐릭 베어 큐브','level':4})
                c['equip_skills'].update(atk_pct=[11.11,11.11,12.34],charge_speed_pct=[2.34,2.34,4.3])
                b['stat_deltas']={character:{'atk':12000,'hp':100000,'def':250}}
            yield name,b,extra
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--output',required=True);ap.add_argument('--fail-fast',action='store_true');args=ap.parse_args()
    files=['research/verify-survival-scaling-real.py','scripts/verify-staged-survival-scaling.py','scripts/staged-survival-scaling-runtime.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/detail_world.py','app/detail_boss.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/data/parsed_skills.json']+['research/staging/v36/app/'+n for n in (('detail_gpu.py','survival_scaling_compat.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json') if args.backend=='ptx' else ('detail_gpu.py','survival_scaling_compat.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'))]
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};rows=[];planned=list(fixtures());device=v.s.v.v.v.Cuda()
    try:
        for name,b,extra in planned:
            try:r=v.compare(device,name,b,extra,args.backend)
            except Exception as exc:r=dict(name=name,passed=False,error=repr(exc));print(json.dumps(r),flush=True)
            rows.append(r)
            if args.fail_fast and not r['passed']:break
    finally:device.close()
    assert hashes=={p:sha(p) for p in files}
    r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(x['passed'] for x in rows),stage_only=True,objective_complete=False,abi=v.g.DETAIL_ABI,backend=args.backend,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
    (ROOT/args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
