"""Cost of an unobserved common notice stream; not overall gameplay speed."""
import argparse,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from test_weapon_mode_specs import effect,chars,NAMES
from gpu_selector import Cuda
import detail_gpu as g
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--baseline');args=ap.parse_args()
program=g.compile_effects(chars(),[(effect('equivalent','instant','squad_ammo_consume_as',40),NAMES[0])]);stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in NAMES}
script=[[0,0,7,0,0,-1,0,0]]*2000+[[0,2,0,0,-1,0,0,0]]
digest=hashlib.sha256(json.dumps(dict(program=program,stats=stats,script=script),sort_keys=True).encode()).hexdigest()
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'tests/test_weapon_mode_specs.py']+[ROOT/'app'/name for name in ('detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json')]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};device=Cuda();samples=[];semantic=None
try:
    g.run(device,[program]*8,script,[[0,0]]*8,[stats]*8,module_backend='native')
    for _ in range(3):
        result=g.run(device,[program]*8,script,[[0,0]]*8,[stats]*8,module_backend='native')
        current=dict(queries=result['queries'],totals=result['totals']);assert all(q[0][0]==0 and q[0][35]==0 and q[0][43]==0 and q[0][44]==120 for q in result['queries'])
        if semantic is not None:assert semantic==current
        semantic=current;samples.append(result['timings_ms']['kernel_cuda'])
finally:device.close()
median=statistics.median(samples);comparison=None
if args.baseline:
    prior=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'));assert prior['passed'] and prior['stimulus_sha256']==digest and prior['semantic']==semantic
    comparison=dict(baseline=args.baseline,kernel_speedup=prior['median_kernel_ms']/median)
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
r=dict(passed=True,scope='2000 authored commands with39 extra notices each, no matching listeners,8 independent interpreters;3 warm samples. Queue cost only, not gameplay.',median_kernel_ms=median,kernel_samples_ms=samples,comparison=comparison,semantic=semantic,stimulus_sha256=digest,source_sha256=before)
(ROOT/args.output).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,median_kernel_ms=median,comparison=comparison)))
