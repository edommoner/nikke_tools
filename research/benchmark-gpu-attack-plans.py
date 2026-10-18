"""GPU group metadata stress, separate from real squad/search performance."""
import argparse,hashlib,importlib.util,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a
from gpu_selector import Cuda
from impact_specs import ActorHandle,ActorKind,HitFamily,HitOutcome,Impact,impact_command
import detail_gpu as g
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--baseline');args=ap.parse_args()
names=['리타','크라운','앨리스','모더니아','N102'];chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in names]
effects=[(dict(name='listener'+str(i),source='스킬1',type='buff',stat='',target='self',duration=-1,trigger=dict(timing=['multi_hit:'+str(1+i%128)],condition=[])),names[0]) for i in range(200)]
program=g.compile_effects(chars,effects);stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in names};iterations=1000
hit=impact_command(0,Impact(names[0],ActorHandle(ActorKind.ADD,0),HitFamily.WEAPON,HitOutcome.DAMAGING,1,1,1),names)
script=[]
for i in range(iterations):script += [[0,10,32,0,1,-1,i+1,0],hit,[0,11,0,0,1,-1,i+1,0]]
script += [[0,2,131,0,1,0,0,0],[0,2,0,0,program['states']['listener0'],1,0,0]]
digest=hashlib.sha256(json.dumps(dict(program=program,stats=stats,script=script),sort_keys=True).encode()).hexdigest()
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve()]+[ROOT/'app'/n for n in ('detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json')]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};device=Cuda();samples=[];semantic=None
try:
    g.run(device,[program]*8,script,[[0,0]]*8,[stats]*8,module_backend='native')
    for _ in range(3):
        result=g.run(device,[program]*8,script,[[0,0]]*8,[stats]*8,module_backend='native')
        current=dict(queries=result['queries'],totals=result['totals'])
        assert all(q[0][:6]==[0,0,0,0,0,iterations] and q[1][37]==1 and q[1][38]==0 for q in result['queries'])
        if semantic is not None:assert semantic==current
        semantic=current;samples.append(result['timings_ms']['kernel_cuda'])
finally:device.close()
median=statistics.median(samples);comparison=None
if args.baseline:
    old=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'));assert old['passed'] and old['stimulus_sha256']==digest and old['semantic']==semantic
    comparison=dict(baseline=args.baseline,kernel_speedup=old['median_kernel_ms']/median)
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=True,scope='200 immutable listener definitions,128 thresholds,1000 explicitly delimited one-target groups,8 independent interpreters;3 warm kernel samples. Metadata stress only, not normal gameplay.',median_kernel_ms=median,kernel_samples_ms=samples,comparison=comparison,semantic=semantic,stimulus_sha256=digest,source_sha256=before)
(ROOT/args.output).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,median_kernel_ms=median,comparison=comparison)))
