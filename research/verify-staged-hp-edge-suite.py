"""Source-bound warm-context HP acceptance; one actual GPU process per backend."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
hp=load('hp_suite_authored','scripts/verify-staged-hp-edge.py');real=load('hp_suite_real','scripts/verify-staged-hp-edge-real.py');ns=load('hp_suite_namespace','scripts/verify-staged-hp-edge-namespace.py')
assert hp.g is real.g is ns.g
files=set(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'scripts').glob('verify-*.py'))
files.update(['research/verify-staged-hp-edge-suite.py','scripts/staged-hp-edge-runtime.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','app/gpu_combat.py','app/gpu_service.py','app/detail_boss.py','app/detail_world.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json'])
files.update('research/staging/v35/app/'+n for n in (('detail_gpu.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json') if args.backend=='ptx' else ('detail_gpu.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json')))
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in sorted(files)}
planned=[(group,verifier,name,b,extra) for group,verifier in (('namespace',ns),('authored',hp),('real',real)) for name,b,extra in verifier.fixtures()];rows=[];device=hp.s.v.v.v.Cuda()
try:
    for group,verifier,name,b,extra in planned:
        try:r=verifier.compare(device,name,b,extra,args.backend)
        except Exception as exc:r=dict(name=name,passed=False,error=repr(exc));print(json.dumps(r),flush=True)
        r['group']=group;rows.append(r)
        if not r['passed']:break
finally:device.close()
assert hashes=={p:sha(p) for p in files},'Sources changed during the acceptance run.'
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(x['passed'] for x in rows),objective_complete=False,stage_only=True,abi=hp.g.DETAIL_ABI,backend=args.backend,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
(ROOT/args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=r['passed'],cases=len(rows),backend=args.backend)),flush=True);raise SystemExit(0 if r['passed'] else 1)
