"""Receiver mutation workload including unrelated resident state markers."""
import argparse,hashlib,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_mutation_cases import prepare,NAMES,world_patterns
from enemy_recipient_cases import field,manager
from detail_coverage import a
from detail_boss import compile_world
from gpu_selector import Cuda
import detail_gpu as g
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--baseline');args=ap.parse_args()
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve()]+[ROOT/p for p in ('scripts/enemy_mutation_cases.py','scripts/enemy_recipient_cases.py','scripts/detail_coverage.py','tests/test_target_counter_runtime.py','app/detail_effects.cu','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json')]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
bm,*_=prepare();effects=[e for e,n in bm._effects];owners=[NAMES.index(n) for e,n in bm._effects]
effects[3]['max_stack']=-1
for i in range(16):effects.append(field(f'resident{i}','',0,'battle_start',stack=1,duration=-1,target='all_enemies'));owners.append(0)
bm=manager(effects,owners)
chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES];program=g.compile_effects(chars,bm._effects,enemy_fields=True);raw=world_patterns();program['world'],_=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},program)
script=[[0,15,0,0,0,-1,0,0],[0,0,0,0,0,-1,0,0]]
for i in range(256):
    for event in (3,7,10,36,23,17):script.append([.01,0,event,0,0,-1,0,0])
for i,wire in enumerate((0,5,13)):script.append([.01,2,135,0,wire,i,12,1])
script += [[.01,2,103,0,6,3,0,0],[.02,5,0,0,0,-1,0,0]]
device=Cuda();samples=[];semantic=None
try:
    for repeat in range(4):
        started=time.perf_counter();result=g.run(device,[program]*8,script,[[0,0]]*8,[bm.state['base_stats']]*8,module_backend='native');elapsed=(time.perf_counter()-started)*1000
        values=[[q[0] for q in squad] for squad in result['queries']];assert values==[[0,0,0,768]]*8,values
        current=dict(values=values,totals=result['totals']);assert all(t==[0]*5 for t in current['totals'])
        if semantic is not None:assert current==semantic
        semantic=current
        if repeat:samples.append(elapsed)
finally:device.close()
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=True,samples_ms=samples,median_ms=statistics.median(samples),semantic=semantic,batch_squads=8,mutation_cycles=256,resident_markers=48,source_sha256=before,scope='GPU receiver mutation workload with host preparation; no weapons or squad damage')
if args.baseline:
    baseline=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'));assert baseline['passed'] and baseline['semantic']==semantic
    report.update(baseline=args.baseline,speedup=baseline['median_ms']/report['median_ms'])
(ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k in ('passed','median_ms','speedup')}))
