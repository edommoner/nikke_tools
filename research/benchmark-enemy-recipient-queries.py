"""CPU reference query cache only; this does not measure a GPU/game speedup."""
import argparse,hashlib,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_recipient_cases import field,NAMES,manager,BossScript,validate,registry_for
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--baseline');args=ap.parse_args()
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/enemy_recipient_cases.py',ROOT/'tests/test_target_counter_runtime.py']
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
effects=[field('field'+str(i),'received_dmg_pct',(i+1)/8,'battle_start',stack=1,duration=10,target='all_enemies') for i in range(32)]
bm=manager(effects);enemy={'def':0,'core_px':0};boss=BossScript(validate([dict(id='wave',kind='summon',spec=dict(count=2,hp=1e9))]),enemy,lambda *_:True);registry_for(bm,boss);boss.begin_frame(0,enemy)
bm.enemy_resolver=lambda target,caster:boss.resolve_enemies(target,bm.enemy_has_state,caster)
bm.notify('battle_start',0,NAMES[0]);labels=['__enemy__']+[a.id for a in boss._runs[0].adds]
samples=[];checksum=None;count=4096;expected=sum((i+1)/8 for i in range(32))*count
for iteration in range(4):
    start=time.perf_counter();value=sum(bm.get_buffs(NAMES[0],labels[i%len(labels)],.1).get('received_dmg',0) for i in range(count));elapsed=(time.perf_counter()-start)*1000
    assert value==expected
    checksum=value
    if iteration:samples.append(elapsed)
assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
stimulus=hashlib.sha256(json.dumps([effects,labels,count],sort_keys=True).encode()).hexdigest()
report=dict(passed=True,cpu_only=True,query_count=count,active_fields=32,recipients=3,checksum=checksum,repetitions=3,ms=samples,median_ms=statistics.median(samples),stimulus_sha256=stimulus,source_sha256=before,overall_speedup_claim=False)
if args.baseline:
    prior=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'));assert prior['passed'] and prior['stimulus_sha256']==stimulus and prior['checksum']==checksum
    report['comparison']=dict(baseline=args.baseline,cpu_query_speedup=prior['median_ms']/report['median_ms'])
(ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,median_ms=report['median_ms'],comparison=report.get('comparison'))))
