"""GPU-only authored pool workload; results must match before/after optimization."""
import argparse,copy,hashlib,importlib.util,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts')]
spec=importlib.util.spec_from_file_location('source_pool_fixture','scripts/verify-periodic-sources-detail.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--baseline');args=parser.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/verify-periodic-sources-detail.py',ROOT/'scripts/detail_coverage.py']
    files += [ROOT/'app'/n for n in ('detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json')]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    effects=[]
    for i in range(64):
        name='channel'+str(i);effects.append(m.source(name,[-1],.1))
        effects.append(m.v.effect('packet'+str(i),'damage','armor_break_damage:'+name,1,event='source_tick:'+name))
    compiled=[]
    with m.v.custom_effects({m.N[0]:effects}):
        for i in range(8):
            body=m.body_for(m.N,2,True);body.update(seed=12345,burst_gauge_mode='fixed',stat_deltas={m.N[0]:{'atk':i*1000}})
            compiled.append(m.a.evaluate({**body,'_compile_gpu_detail':True}))
    digest=lambda:hashlib.sha256(json.dumps([{key:entry[key] for key in ('program','base_stats','enemy','body')} for entry in compiled],ensure_ascii=True).encode()).hexdigest()
    program_sha256=digest();device=m.Cuda();samples=[];results=None
    project=lambda row:{key:row.get(key) for key in ('total_damage','members','base_stats','burst_timeline','parts_state','seed','shooting_policy','burst_gauge_mode')}
    try:
        m.g.evaluate_full_many(device,compiled,module_backend='native')
        for _ in range(3):
            started=time.perf_counter();outputs=m.g.evaluate_full_many(device,compiled,module_backend='native');elapsed=(time.perf_counter()-started)*1000
            current=[project(row) for row in outputs]
            if results is not None:assert current==results
            results=current;samples.append(dict(wall_ms=elapsed,kernel_ms=outputs[0]['compute']['timings_ms']['kernel_cuda']))
    finally:device.close()
    assert digest()==program_sha256
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    median=statistics.median(row['kernel_ms'] for row in samples);comparison=None
    if args.baseline:
        baseline=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'));assert baseline['passed'] and baseline['program_sha256']==program_sha256 and baseline['results']==results
        comparison=dict(baseline=args.baseline,kernel_speedup=baseline['median_kernel_ms']/median)
    report=dict(passed=True,scope='Authored maximum64-channel workload,8 independent squads,2 seconds of autonomous combat. GPU-only; warm context;3 measured repetitions. Not representative gameplay.',
        samples=samples,median_kernel_ms=median,results=results,program_sha256=program_sha256,comparison=comparison,source_stable=True,source_sha256=before)
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,median_kernel_ms=median,comparison=comparison)),flush=True)

if __name__=='__main__':main()
