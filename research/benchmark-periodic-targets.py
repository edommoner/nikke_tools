"""Timer work with unrelated definitions; CUDA events separate host preparation."""
import argparse,hashlib,importlib.util,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_recipient_cases import field,manager,NAMES
from enemy_mutation_cases import instant
from detail_coverage import a
from gpu_selector import Cuda
import detail_gpu as g
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--baseline');ap.add_argument('--baseline-engine');ap.add_argument('--family',choices=('instant','damage'),default='instant');args=ap.parse_args()
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve()]+[ROOT/p for p in ('scripts/enemy_mutation_cases.py','scripts/enemy_recipient_cases.py','scripts/detail_coverage.py','tests/test_target_counter_runtime.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json')]
old=None
if args.baseline_engine:
    source=ROOT/args.baseline_engine;spec=importlib.util.spec_from_file_location('periodic_perf_before',source);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    files += [source]+[source.parent/n for n in ('detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json')]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
effects=[field('payload','received_dmg_pct',10,'battle_start',stack=-1,duration=20,target='boss')]
for i in range(16):effects.append(instant(f'timer{i}','debuff_stack_add','burst_cast',target='boss',reference='payload',value=1,tick_interval=.125,duration=20))
if args.family=='damage':
    effects=[field('no critical','crit_rate',-15,'battle_start',stack=1,duration=-1,target='self')]
    for i in range(16):effects.append(dict(name=f'timer{i}',source='스킬1',type='damage',stat='dot_damage',fixed_value=100,target='target',tick_interval=.125,duration=20,trigger=dict(timing=['battle_start'],condition=[])))
for i in range(80):effects.append(field(f'resident{i}','',0,'battle_start',stack=1,duration=-1,target='self'))
bm=manager(effects,[0]*len(effects));chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES];program=g.compile_effects(chars,bm._effects,enemy_fields=True)
script=[[0,0,0,0,0,-1,0,0],[0,0,3,0,0,-1,0,0]]+[[i*.125,15,0,0,0,-1,0,0] for i in range(129)]
# Time0 world frame precedes activation; the remaining frames drive the clocks.
script=[script[2]]+script[:2]+script[3:]+([[16,2,135,0,0,0,12,1]] if args.family=='instant' else [[16,2,0,0,-1,0,0,0]])+[[16.01,5,0,0,0,-1,0,0]]
stimulus_sha256=hashlib.sha256(json.dumps([program,script,bm.state['base_stats']],sort_keys=True,ensure_ascii=True).encode()).hexdigest()
device=Cuda();semantic=None
def once(engine):
    global semantic
    started=time.perf_counter();result=engine.run(device,[program]*8,script,[[0,0]]*8,[bm.state['base_stats']]*8,module_backend='native');wall=(time.perf_counter()-started)*1000
    value=dict(queries=result['queries'],totals=result['totals'])
    if args.family=='instant':
        assert [q[0][0] for q in result['queries']]==[20490]*8
        assert result['totals']==[[0]*5]*8
    else:
        assert [q[0][38] for q in result['queries']]==[2048000]*8
        assert result['totals']==[[2048000,0,0,0,0]]*8
    if semantic is not None:assert value==semantic
    semantic=value
    return dict(wall_ms=wall,kernel_ms=result['timings_ms']['kernel_cuda'])
try:
    once(g)
    if old:once(old)
    samples=[];old_samples=[]
    for i in range(5 if old else 3):
        for label,engine in ([('old',old),('current',g)] if old and i%2==0 else [('current',g),('old',old)] if old else [('current',g)]):
            result=once(engine);(old_samples if label=='old' else samples).append(result)
finally:device.close()
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=True,source_sha256=before,stimulus_sha256=stimulus_sha256,semantic=semantic,samples=samples,median_kernel_ms=statistics.median(r['kernel_ms'] for r in samples),median_wall_ms=statistics.median(r['wall_ms'] for r in samples),family=args.family,scope=f'8 squads, 16 {args.family} timers, 80 unrelated definitions, 128 firing frames; no weapon execution')
if args.baseline:
    prior=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'));assert prior['passed'] and prior['stimulus_sha256']==stimulus_sha256 and prior['semantic']==semantic
    report.update(baseline=args.baseline,historical_kernel_ms=prior['median_kernel_ms'])
if old:
    report.update(interleaved=True,baseline_engine=args.baseline_engine,old_samples=old_samples,before_kernel_ms=statistics.median(r['kernel_ms'] for r in old_samples),before_wall_ms=statistics.median(r['wall_ms'] for r in old_samples))
    report['kernel_speedup']=report['before_kernel_ms']/report['median_kernel_ms'];report['wall_speedup']=report['before_wall_ms']/report['median_wall_ms']
(ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k in ('passed','median_kernel_ms','median_wall_ms','kernel_speedup','wall_speedup')}))
