"""GPU shared receiver update workload, separate from whole-squad throughput."""
import argparse,hashlib,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_fanout_cases import selector_prepare,NAMES,world_patterns
from detail_coverage import a
from detail_boss import compile_world
from gpu_selector import Cuda
import detail_gpu as g
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--baseline');args=ap.parse_args()
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve()]+[ROOT/p for p in ('scripts/enemy_fanout_cases.py','scripts/enemy_recipient_cases.py','scripts/detail_coverage.py','tests/test_target_counter_runtime.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json')]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
bm,*_=selector_prepare();bm._effects[0][0].pop('max_trigger');bm._effects[2][0]['max_stack']=-1
chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES];program=g.compile_effects(chars,bm._effects,enemy_fields=True);raw=world_patterns();program['world'],_=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},program)
script=[[0,15,0,0,0,-1,0,0]]+[[.01,0,3,0,0,-1,0,0] for _ in range(512)]
for i,wire in enumerate((0,5,13)):script.append([.01,2,135,0,wire,i,12,1])
script += [[.01,2,103,0,6,3,0,0],[.02,5,0,0,0,-1,0,0]]
device=Cuda();samples=[];semantic=None
try:
    for repeat in range(4):
        started=time.perf_counter();result=g.run(device,[program]*8,script,[[0,0]]*8,[bm.state['base_stats']]*8,module_backend='native');elapsed=(time.perf_counter()-started)*1000
        values=[[q[0] for q in squad] for squad in result['queries']]
        assert values==[[30,30,30,1536]]*8,values
        current=dict(values=values,totals=result['totals']);assert all(t==[0]*5 for t in current['totals'])
        if semantic is not None:assert current==semantic
        semantic=current
        if repeat:samples.append(elapsed)
finally:device.close()
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=True,samples_ms=samples,median_ms=statistics.median(samples),semantic=semantic,batch_squads=8,notifications=512,source_sha256=before,scope='GPU shared receiver updates, no weapons or squad damage')
if args.baseline:
    baseline=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'));assert baseline['passed'] and baseline['semantic']==semantic
    report.update(baseline=args.baseline,speedup=baseline['median_ms']/report['median_ms'])
(ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k in ('passed','median_ms','speedup')}))
