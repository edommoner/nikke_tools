"""Run the accepted v38 101-case suite against staged v39/CPU extension."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=load('outgoing_regression_runtime','scripts/staged-outgoing-healing-runtime.py').install()
r=load('outgoing_previous_regressions','scripts/verify-decoy-healing-regressions.py');d=r.d
def fixtures():
    result=[(d,*x) for x in d.fixtures()]+[(d,*x) for x in d.real_fixtures()]+r.fixtures()
    assert len(result)==101;return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx'],required=True);p.add_argument('--output',required=True);args=p.parse_args()
    files=['research/verify-outgoing-healing-regressions.py','scripts/staged-outgoing-healing-runtime.py','scripts/verify-decoy-healing-regressions.py','scripts/verify-decoy-healing.py','scripts/verify-cover-capacity.py','scripts/verify-survival-scaling.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','scripts/audit-incoming-damage.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','app/detail_world.py','app/detail_boss.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json','research/upstream/nikke-calc-master/data/base_stat_tables/cube.json','research/upstream/nikke-calc-master/runner/spec.py']
    files+=['research/staging/v39/app/'+n for n in (['detail_gpu.py','outgoing_healing_compat.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json'] if args.backend=='ptx' else ['detail_gpu.py','outgoing_healing_compat.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'])]
    sha=lambda path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest();hashes={path:sha(path) for path in files};planned=fixtures();rows=[];device=d.v.s.v.v.v.Cuda()
    try:
        for oracle,name,b,extra in planned:
            try:row=oracle.compare(device,name,b,extra,args.backend)
            except Exception as e:row=dict(name=name,passed=False,error=repr(e));print(json.dumps(row),flush=True)
            rows.append(row)
            if not row['passed']:break
    finally:device.close()
    assert hashes=={path:sha(path) for path in files}
    result=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==101 and all(x['passed'] for x in rows),stage_only=True,objective_complete=False,abi=g.DETAIL_ABI,backend=args.backend,planned_cases=101,cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False,cpu_model_extended=True)
    (ROOT/args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if result['passed'] else 1)
