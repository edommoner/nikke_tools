"""Before/after benchmark for shared staged queues; immutable GPU inputs only."""
import argparse,hashlib,importlib.util,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts')]
spec=importlib.util.spec_from_file_location('staged_workload','scripts/verify-staged-dot-detail.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--baseline');args=parser.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/verify-staged-dot-detail.py',ROOT/'scripts/detail_coverage.py']
    files += [ROOT/'app'/name for name in ('detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json')]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    parent,_=m.definition(16);effects=[m.E('no critical','buff','crit_rate',-15,'all_allies'),parent]
    for i in range(64):
        _,dot=m.definition(16,1,16);dot.update(name='staged'+str(i),ramp_interval=.01,fixed_value=1)
        effects.append(dot)
    compiled=[]
    with m.v.custom_effects({m.N[0]:effects}):
        for i in range(8):
            body=m.body_for(m.N,2,True);body.update(seed=12345,burst_gauge_mode='fixed',stat_deltas={m.N[0]:{'atk':i*1000}})
            compiled.append(m.a.evaluate({**body,'_compile_gpu_detail':True}))
    digest=lambda:hashlib.sha256(json.dumps([{key:c[key] for key in ('program','base_stats','enemy','body')} for c in compiled],ensure_ascii=True).encode()).hexdigest()
    program_sha256=digest();device=m.Cuda();samples=[];results=None
    project=lambda r:{key:r.get(key) for key in ('total_damage','members','base_stats','burst_timeline','parts_state','seed','shooting_policy','burst_gauge_mode')}
    try:
        m.g.evaluate_full_many(device,compiled,module_backend='native')
        for _ in range(3):
            start=time.perf_counter();outputs=m.g.evaluate_full_many(device,compiled,module_backend='native')
            current=[project(row) for row in outputs]
            if results is not None:assert results==current
            results=current;samples.append(dict(wall_ms=(time.perf_counter()-start)*1000,kernel_ms=outputs[0]['compute']['timings_ms']['kernel_cuda']))
    finally:device.close()
    assert digest()==program_sha256 and before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    median=statistics.median(row['kernel_ms'] for row in samples);comparison=None
    if args.baseline:
        old=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'));assert old['passed'] and old['program_sha256']==program_sha256 and old['results']==results
        comparison=dict(baseline=args.baseline,kernel_speedup=old['median_kernel_ms']/median)
    report=dict(passed=True,scope='Authored64 simultaneous staged DoTs,16 steps each;8 autonomous2-second squads;3 warm measured repetitions. Not representative gameplay.',samples=samples,median_kernel_ms=median,results=results,program_sha256=program_sha256,comparison=comparison,source_stable=True,source_sha256=before)
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,median_kernel_ms=median,comparison=comparison)),flush=True)

if __name__=='__main__':main()
