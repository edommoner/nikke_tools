"""CPU carrier executor overhead; not GPU or normal squad throughput."""
import argparse,hashlib,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_fanout_cases import prepare,NAMES
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--baseline');args=ap.parse_args()
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve()]+[ROOT/p for p in ('scripts/enemy_fanout_cases.py','scripts/enemy_recipient_cases.py','tests/test_target_counter_runtime.py')]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
samples=[];values=[]
for _ in range(3):
    bm,boss,enemy,effect=prepare();boss.begin_frame(0,enemy)
    effect.pop('max_trigger');effect['name']='';effect['max_stack']=-1
    labels=['__enemy__']+[a.id for a in boss._runs[0].adds]
    sets=[labels[:2],labels[1:],[labels[2]]]
    started=time.perf_counter()
    for i in range(4096):bm._activate(effect,NAMES[0],0,targets=sets[i%3])
    samples.append((time.perf_counter()-started)*1000)
    values.append([bm.get_buffs(NAMES[0],label,0).get('received_dmg',0) for label in labels])
assert values==[[13660,27310,27300]]*3,values
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=True,cpu_only=True,samples_ms=samples,median_ms=statistics.median(samples),values=values,original_activations=4096,source_sha256=before,scope='CPU overlapping receiver carrier updates, no named children or squad damage')
if args.baseline:
    baseline=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'));assert baseline['passed'] and baseline['values']==values
    report.update(baseline=args.baseline,speedup=baseline['median_ms']/report['median_ms'])
(ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k in ('passed','median_ms','speedup')}))
