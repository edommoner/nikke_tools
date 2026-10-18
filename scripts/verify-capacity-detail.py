"""Effect-ID boundaries and rich, unmodified-skill whole squads against CPU."""
import argparse,copy,hashlib,importlib.util,json,math,random,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import detail_gpu as g
from gpu_selector import Cuda
from gpu_service import resolve_verification
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=load('capacity_counts','scripts/verify-counts-detail.py')
t=load('capacity_team','scripts/verify-team-hits-detail.py')
E=c.E;NAMES=c.NAMES
def fillers(n):
    return [(E('capacity inert '+str(i),'buff','atk_pct',0,event='inactive'),NAMES[0]) for i in range(n)]
def primitives():
    for boundary in (31,32,127,128,255):
        effects=fillers(256)
        effects[boundary]=(E('high reducer','buff','trigger_count_reduce',2,target_effect='high listener'),NAMES[0])
        listener=128 if boundary!=128 else 127
        effects[listener]=(E('high listener','buff','atk_pct',1,event='on_attack_count:5',max_stack=1000),NAMES[0])
        p=c.oracle.program(c.oracle.characters(NAMES),effects)
        assert int(p['effects'][listener][g.REDUCER_MASK+boundary//32])&(1<<(boundary%32))
        assert p['states']['high listener']>=127
        script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+[[(i+1)/10,0,7,0,0,-1,0,0] for i in range(9)]
        script.append([1,2,0,0,p['states']['high listener'],0,0,0])
        yield 'reducer-id-'+str(boundary),p,script,3
    # Expanded attacker definitions must keep shared budgets above the old cap.
    effects=fillers(129)
    source=NAMES[0]
    effects.append((E('high team budget','buff','atk_pct',7,'all_allies',event='body_hit_count:1',max_trigger=3,max_stack=10),source))
    p=c.oracle.program(c.oracle.characters(NAMES),effects)
    assert all(row[269]==130 for row in p['effects'][129:134])
    script=[[0,0,0,i,0,-1,0,0] for i in range(5)]
    for i,attacker in enumerate((4,0,2,3,1,4,0),1):script.append([i/10,0,45,attacker,-1,-1,0,0])
    script.append([1,2,0,0,p['states']['high team budget'],0,0,0])
    yield 'team-shared-budget-id-129',p,script,None
def verify_primitives(device,backend):
    rows=[];stats={n:{'atk':100000,'def':20000,'hp':1000000} for n in NAMES}
    for name,p,script,count in primitives():
        with t.manual_team_events():cpu,totals=t.oracle.oracle(p,script,[31784,0],stats)
        gpu=g.run(device,[p],script,[[31784,0]],[stats],module_backend=backend)
        checks=dict(queries=all(math.isclose(x[k],y[k],rel_tol=1e-12,abs_tol=1e-8) for x,y in zip(cpu,gpu['queries'][0]) for k in list(range(32))+[36,37]),totals=totals==gpu['totals'][0])
        if count is not None:checks['expected_count']=cpu[0][37]==gpu['queries'][0][0][37]==count
        row=dict(name=name,backend=backend,kind='primitive',effects=len(p['effects']),checks=checks,passed=all(checks.values()),cpu_queries=cpu,gpu_queries=gpu['queries'][0]);rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k not in ('cpu_queries','gpu_queries')},ensure_ascii=True),flush=True)
    return rows
def rich_fixture():
    fixture=json.loads((ROOT/'research/detail-team-hits-api-fixture.json').read_text(encoding='utf-8'))
    previous=json.loads((ROOT/'research/ports/v28/research/detail-capacity-cpu-audit.json').read_text(encoding='utf-8'))['burst_chain_example']
    growth=fixture['profile']['chars'][fixture['squad'][0]]
    body=copy.deepcopy(fixture);body['squad']=[r['character'] for r in previous['characters']]
    body['profile']['chars']={r['character']:{**copy.deepcopy(growth),'favorite_stage':r['favorite']} for r in previous['characters']}
    body.update(patches={},stat_deltas={},duration=31,burst_policy='auto',shooting_policy='character',burst_gauge_mode='accumulate',seed=12345)
    return body
def verify_battles(device,backend,long=False):
    rows=[];fixture=rich_fixture()
    templates=[]
    for policy in ('auto','rules'):
        for shooting in ('auto','character'):
            for gauge in ('fixed','accumulate'):
                body=copy.deepcopy(fixture);body.update(burst_policy=policy,shooting_policy=shooting,burst_gauge_mode=gauge)
                templates.append(('rich-'+policy+'-'+shooting+'-'+gauge,body,{}))
    # Real Vesti B3 damage with later buffs whose definition IDs exceed 128.
    body=t.body_for(['리타','크라운','베스티','앨리스','모더니아'],31,True)
    body.update(burst_policy='auto',shooting_policy='character',burst_gauge_mode='accumulate',seed=12345)
    extra={body['squad'][0]:[e for e,n in fillers(129)]}
    templates.append(('high-B3-exclusion',body,extra))
    if long:
        body=copy.deepcopy(fixture);body['duration']=180;templates=[('rich-180',body,{})]
    for name,body,extra in templates:
        body['_debug_random_state']=True
        with t.raw.injected_effects(extra):
            compiled=t.a.evaluate({**body,'_compile_gpu_detail':True})
            if name=='high-B3-exclusion':
                deferred=[r for r in compiled['program']['effects'] if r[51]]
                assert deferred and any(any(r[g.B3_MASK+i] for i in range(4,8)) for r in deferred)
            assert len(compiled['program']['effects'])>128
            gpu=g.evaluate_full(device,compiled,module_backend=backend);cpu=t.a.evaluate(body);rng=list(random.getstate()[1])
        result=resolve_verification(gpu,cpu);checks=result['compute']['cpu_verification'].copy()
        checks.update(actual_gpu=result['compute']['backend']=='cuda_detail',final_random_state=rng==gpu['_random_state'],burst_exercised=bool(cpu['burst_timeline']))
        row=dict(name=name,backend=backend,kind='battle',duration=body['duration'],effects=len(compiled['program']['effects']),states=len(compiled['program']['states']),checks=checks,passed=all(checks.values()),cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],cpu_members=cpu['members'],gpu_members=gpu['members'],workspace_bytes=gpu['compute'].get('workspace_bytes'))
        rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
    return rows
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx','both'],default='both');ap.add_argument('--long',action='store_true');ap.add_argument('--output',default='research/detail-capacity-verification.json');args=ap.parse_args()
    files=['scripts/verify-capacity-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    device=Cuda()
    try:rows=[r for backend in (('native','ptx') if args.backend=='both' else (args.backend,)) for r in ([] if args.long else verify_primitives(device,backend))+verify_battles(device,backend,args.long)]
    finally:device.close()
    assert hashes=={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=bool(rows) and all(r['passed'] for r in rows),objective_complete=False,cases=rows,cpu_trace_used_as_gpu_input=False,source_sha256=hashes)
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
