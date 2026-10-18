"""Accepted v39 authored19/raw4/prior101 against v40 CPU/GPU implementation."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
g=load('storage_regression_runtime','scripts/staged-healing-storage-runtime.py').install()
out=load('storage_outgoing_regressions','scripts/verify-outgoing-healing.py');old=load('storage_prior_regressions','scripts/verify-outgoing-healing-regressions.py')
def fixtures():
    cases=[(out,*x) for x in out.fixtures()]+[(out,*x) for x in out.real_fixtures()]+old.fixtures();assert len(cases)==124;return cases
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
    files=['research/verify-healing-storage-regressions.py','scripts/staged-healing-storage-runtime.py','scripts/verify-outgoing-healing.py','scripts/verify-outgoing-healing-regressions.py','scripts/verify-decoy-healing.py','scripts/verify-decoy-healing-regressions.py','scripts/verify-cover-capacity.py','scripts/verify-survival-scaling.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','scripts/audit-incoming-damage.py','app/engine_worker.py','app/engine_compat.py','app/outgoing_healing_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','app/detail_world.py','app/detail_boss.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json','research/upstream/nikke-calc-master/data/base_stat_tables/cube.json','research/upstream/nikke-calc-master/runner/spec.py']
    files+=['research/staging/v40/app/'+n for n in (['healing_storage_compat.py','detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json'] if args.backend=='ptx' else ['healing_storage_compat.py','detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'])]
    sha=lambda f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest();hashes={f:sha(f) for f in files};planned=fixtures();rows=[];device=out.v.s.v.v.v.Cuda()
    try:
        for oracle,name,b,x in planned:
            try:row=oracle.compare(device,name,b,x,args.backend)
            except Exception as e:row=dict(name=name,passed=False,error=repr(e));print(json.dumps(row),flush=True)
            rows.append(row)
            if not row['passed']:break
    finally:device.close()
    assert hashes=={f:sha(f) for f in files}
    r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==124 and all(x['passed'] for x in rows),abi=g.DETAIL_ABI,backend=args.backend,planned_cases=124,not_run_cases=124-len(rows),cases=rows,cpu_model_extended=True,in_game_rules_verified=False,cpu_trace_used_as_gpu_input=False,stage_only=True,objective_complete=False,source_sha256=hashes)
    (ROOT/args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
