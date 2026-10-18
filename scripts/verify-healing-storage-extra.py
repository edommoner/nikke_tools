"""Additional storage parity and actual workspace size, GPU executes first."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sp=importlib.util.spec_from_file_location('storage_extra_gpu_fixtures',ROOT/'scripts/healing-storage-extra-fixtures.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d);m=d.m;g=m.g
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx'],required=True);p.add_argument('--output',required=True);args=p.parse_args()
    files=['scripts/verify-healing-storage-extra.py','scripts/healing-storage-extra-fixtures.py','scripts/verify-healing-storage.py','scripts/healing-storage-fixtures.py','scripts/verify-survival-scaling.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','app/outgoing_healing_compat.py','app/survival_compat.py','app/survival_scaling_compat.py','app/detail_world.py','app/detail_boss.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']
    files+=['app/'+n for n in (['healing_storage_compat.py','detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json'] if args.backend=='ptx' else ['healing_storage_compat.py','detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'])]
    sha=lambda f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest();hashes={f:sha(f) for f in files};planned=list(d.fixtures());rows=[];sizes=[];device=m.v.s.v.v.v.Cuda();original=g.evaluate_full
    def evaluate(*args,**kwargs):
        result=original(*args,**kwargs);size=result['compute']['workspace_bytes'];sizes.append(size);assert size==1078280,(size,'Unexpected storage workspace layout');return result
    try:
        with patch.object(g,'evaluate_full',evaluate):
            for name,b,x in planned:
                try:row=m.compare(device,name,b,x,args.backend)
                except Exception as e:row=dict(name=name,passed=False,error=repr(e));print(json.dumps(row),flush=True)
                rows.append(row)
                if not row['passed']:break
    finally:device.close()
    assert hashes=={f:sha(f) for f in files}
    r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(x['passed'] for x in rows),abi=g.DETAIL_ABI,backend=args.backend,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,actual_workspace_bytes_per_squad=sorted(set(sizes)),cpu_model_extended=True,in_game_rules_verified=False,cpu_trace_used_as_gpu_input=False,stage_only=False,objective_complete=False,source_sha256=hashes)
    (ROOT/args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
