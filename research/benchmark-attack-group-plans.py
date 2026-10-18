"""CPU metadata-planning cost, separately from any GPU or gameplay claim."""
import argparse,hashlib,json,statistics,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker
from attack_group_runtime import begin,finish
from effect_runtime import pool,publish_impact
from impact_specs import Impact,ActorHandle,ActorKind,HitFamily,HitOutcome

ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--baseline');args=ap.parse_args()
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve()];before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
effects=[(dict(name='effect'+str(i),trigger=dict(timing=['inactive'])), 'A') for i in range(200)]
effects[0][0]['trigger']['timing']=['multi_hit:2'];effects[1][0]['trigger']['timing']=['multi_hit:3']
stimulus=dict(iterations=5000,effects=effects,target=[0,0,1],listeners=[['multi_hit:2',2],['multi_hit:3',3]])
digest=hashlib.sha256(json.dumps(stimulus,sort_keys=True).encode()).hexdigest();samples=[]
for _ in range(3):
    def unexpected(*args,**kwargs):raise AssertionError('One distinct target cannot satisfy two')
    manager=SimpleNamespace(_effects=effects,notify=unexpected);packet=Impact('A',ActorHandle(ActorKind.BODY,0),HitFamily.WEAPON,HitOutcome.DAMAGING,100,1,1)
    start=time.perf_counter();checksum=0
    for index in range(stimulus['iterations']):
        frame=begin(manager,'A',1,0,kinds=[ActorKind.BODY]);publish_impact(manager,packet,0);result=finish(manager,frame,0)
        assert frame.listeners==(('multi_hit:2',2),('multi_hit:3',3));checksum+=len(result.targets)
    samples.append((time.perf_counter()-start)*1000);assert checksum==5000 and not pool(manager,'attack_groups')
median=statistics.median(samples);comparison=None
if args.baseline:
    old=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'));assert old['passed'] and old['stimulus_sha256']==digest and old['checksum']==checksum
    comparison=dict(baseline=args.baseline,speedup=old['median_ms']/median)
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=True,scope='CPU-only common attack-group metadata planning and typed impact delivery; no autonomous weapon producer or GPU speed claim.',samples_ms=samples,median_ms=median,checksum=checksum,stimulus_sha256=digest,comparison=comparison,source_sha256=before)
(ROOT/args.output).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,median_ms=median,comparison=comparison)))
