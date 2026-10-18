"""Debuff immunity in independent complete five-member CPU/GPU battles."""
import copy,hashlib,importlib.util,json,random,sys
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('immune_raw',ROOT/'scripts/verify-cleanse-detail.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
c=r.v.c;E=c.E;NAMES=c.NAMES
import detail_gpu
from calculator.buff_manager import BuffManager
from gpu_selector import Cuda

def scenarios():
    owner=NAMES[0]
    def guard(name='pool',stat='debuff_immune_count',value=1,target='all_allies',**kw):return E(name,'buff',stat,value,target,**kw)
    def harm(name='harm',target='all_allies',**kw):return E(name,'buff','atk_pct',-35,target,**{'event':'every:0.5s','duration':2,'polarity':'harmful',**kw})
    for stat,value in [('debuff_immune',0),('debuff_immune_count',1),('debuff_immune_count',1.5),('debuff_immune_count',0),('debuff_immune_count',-1)]:
        yield stat+'-capacity-'+str(value),{owner:[guard(stat=stat,value=value),harm()]},5,False
    yield 'named-exact-and-other-name',{owner:[guard(stat='debuff_immune:harm'),harm(),harm('other harm')]},5,False
    yield 'empty-name-never-matches-named-immunity',{owner:[guard(stat='debuff_immune:'),harm('')]},5,False
    yield 'same-name-across-casters-uses-max-not-sum',{owner:[guard(value=1),harm()],NAMES[1]:[guard(value=2)]},5,False
    yield 'ordered-distinct-pools',{owner:[guard('first'),guard('second',value=2),harm()]},5,False
    yield 'duplicate-recipients-spend-per-occurrence',{owner:[guard(target='self'),harm(target=[owner,owner,NAMES[1]])]},5,False
    yield 'full-immunity-does-not-spend-count-pool',{owner:[guard(),guard('all immunity','debuff_immune'),harm()]},5,False
    yield 'irremovable-and-beneficial-bypass',{owner:[guard(stat='debuff_immune'),harm(polarity='harmful_irremovable'),harm('negative beneficial',polarity='beneficial')]},5,False
    yield 'lazy-harm-bypasses-application-filter',{owner:[guard(stat='debuff_immune'),harm(target='allies_top_atk:2')]},5,False
    yield 'conditional-presence-not-runtime-gate',{owner:[guard(stat='debuff_immune',event='passive',condition=['during_full_burst']),harm()]},5,False
    yield 'blocked-application-still-spends-trigger-budget',{owner:[guard(stat='debuff_immune',duration=1),harm(max_trigger=1)]},5,False
    yield 'expiry-then-recharge',{owner:[guard(duration=1),guard(event='every:2s',duration=1),harm()]},5,False
    yield 'stacked-recharge',{owner:[guard(event='every:1s',max_stack=3),harm(event='every:0.25s')]},5,False
    yield 'nested-harm-before-recharge-reset',{owner:[guard(),harm(),guard(event='every:1s'),harm('nested',event='event:pool',target=owner)]},5,False
    yield 'lazy-count-is-not-forced-by-immunity-check',{owner:[guard(target='allies_random:2'),harm()]},5,False
    yield 'enemy-target-without-immunity',{owner:[harm(target='target')]},5,False
    yield 'enemy-target-general-immunity',{owner:[guard(stat='debuff_immune',target='target'),harm(target='target')]},5,False
    yield 'enemy-target-named-immunity',{owner:[guard(stat='debuff_immune:harm',target='target'),harm(target='target')]},5,False
    yield 'enemy-target-count-refresh',{owner:[guard(target='target'),guard(target='target',event='every:1s'),harm(target='target')]},5,False
    for who in ['에이드','밀크 : 블루밍 바니']:
        # Keep every real source skill. The authored harmful skill supplies a
        # positive/negative immunity stimulus without inventing boss HP damage.
        effects={'리타':[harm('부끄러움',event='every:1s',duration=1.25)]}
        yield 'raw-'+who,effects,60,who

def body_for(subject,seconds):
    names=[subject,'리타','크라운','앨리스','모더니아'] if subject else NAMES
    body=c.body_for(names,seconds,True)
    body.update(shooting_policy='character',burst_policy='rules',_debug_random_state=True)
    if subject:
        body['profile']['chars'][subject]['equip_skills']['max_ammo_pct']=200
        body['stat_deltas']={subject:{'atk':1234}}
    return body

@contextmanager
def observed():
    blocked=BuffManager._harmful_blocked;activate=BuffManager._activate;events={'blocked':0,'allowed':0,'recharges':[]}
    def check(self,who,eff):
        result=blocked(self,who,eff);events['blocked' if result else 'allowed']+=1;return result
    def application(self,eff,caster,t,*args,**kwargs):
        result=activate(self,eff,caster,t,*args,**kwargs)
        if eff.get('stat')=='debuff_immune_count':events['recharges'].append([caster,eff.get('name',''),t])
        return result
    with patch.object(BuffManager,'_harmful_blocked',check),patch.object(BuffManager,'_activate',application),c.observe() as (_,manager,_):yield events,manager

def compare(device,label,effects,seconds,subject,seed,mode,backend,cpu_only=False):
    body=body_for(subject,seconds);body.update(seed=seed,burst_gauge_mode=mode)
    context=r.injected_effects(effects) if subject else c.p.custom_effects(effects)
    with context:
        compiled=c.a.evaluate({**body,'_compile_gpu_detail':True})
        keys=[name for name in compiled['program']['states']]
        if not cpu_only:
            old_run=detail_gpu.run;captured={}
            def run(device,programs,script,*args,**kwargs):
                script=copy.deepcopy(script);offset=sum(row[1]==2 for row in script)
                for i,name in enumerate(keys):script.append([seconds,2,112,0,compiled['program']['states'][name],offset+i,0,0])
                result=old_run(device,programs,script,*args,**kwargs);captured['pools']=dict(zip(keys,result['queries'][0][offset:]));return result
            with patch.object(detail_gpu,'run',run):gpu=detail_gpu.evaluate_full(device,compiled,module_backend=backend)
        with observed() as (events,manager):cpu=c.a.evaluate(body)
        rng=list(random.getstate()[1]);bm=manager['bm']
    names=body['squad']+['__enemy__']
    pools={key:[bm._immune_used.get((who,key),0) for who in names] for key in keys}
    if cpu_only:return dict(name=label,cpu_total=cpu['total_damage'],events=events,used=pools)
    checks={key:cpu[key]==gpu[key] for key in ('total_damage','members','base_stats','burst_timeline','burst_gauge_mode','seed')}
    checks['final_random_state']=rng==gpu['_random_state']
    errors=[]
    for key,expected in pools.items():
        if list(captured['pools'][key][:6])!=expected:errors.append([key,captured['pools'][key][:6],expected])
    checks['per_name_per_recipient_used']=not errors
    if subject:
        checks['positive_immunity_exercised']=events['blocked']>0
        checks['negative_immunity_exercised']=events['allowed']>0
        if subject=='에이드':checks['real_attack_count_recharge_exercised']=any(t>0 for caster,name,t in events['recharges'] if caster==subject)
    return dict(name=label,seed=seed,mode=mode,backend=backend,passed=all(checks.values()),checks=checks,
                errors=errors,cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],observed=events,
                all_real_skills_retained=bool(subject))

def verify(device,backend,quick=False,cpu_only=False):
    rows=[]
    for label,effects,seconds,subject in scenarios():
        if quick and subject:continue
        for seed in ((0,12345) if subject and not cpu_only else (0,)):
            for mode in (('fixed',) if quick or cpu_only else ('fixed','accumulate')):
                try:row=compare(device,label,effects,seconds,subject,seed,mode,backend,cpu_only)
                except Exception as error:row=dict(name=label,backend=backend,seed=seed,mode=mode,passed=False,error=str(error))
                rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
    return rows

def cpu_assertions(rows):
    by={row['name']:row for row in rows}
    for label,cap in [('debuff_immune_count-capacity-1',1),('debuff_immune_count-capacity-1.5',2),('same-name-across-casters-uses-max-not-sum',2)]:
        assert by[label]['used']['pool']==[cap]*5+[0],label
    assert by['duplicate-recipients-spend-per-occurrence']['used']['pool']==[1,0,0,0,0,0]
    assert by['ordered-distinct-pools']['used']['first']==[1]*5+[0]
    assert by['ordered-distinct-pools']['used']['second']==[2]*5+[0]
    for label in ['debuff_immune-capacity-0','full-immunity-does-not-spend-count-pool','conditional-presence-not-runtime-gate']:
        assert by[label]['events']['blocked']>0 and by[label]['events']['allowed']==0,label
    assert not any(by['full-immunity-does-not-spend-count-pool']['used']['pool'])
    assert by['blocked-application-still-spends-trigger-budget']['events']['blocked']==5
    for label in ['irremovable-and-beneficial-bypass','lazy-harm-bypasses-application-filter']:
        assert by[label]['events']['blocked']==by[label]['events']['allowed']==0
    for label in ['raw-에이드','raw-밀크 : 블루밍 바니']:
        assert by[label]['events']['blocked']>0 and by[label]['events']['allowed']>0
    assert any(t>0 for who,name,t in by['raw-에이드']['events']['recharges'])
    assert by['enemy-target-without-immunity']['events']['blocked']==0
    assert by['enemy-target-count-refresh']['used']['pool']==[0,0,0,0,0,1]
    for label in ['enemy-target-general-immunity','enemy-target-named-immunity']:
        assert by[label]['events']['blocked']>0 and by[label]['events']['allowed']==0,label

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--backend',choices=['native','ptx','both'],default='both');p.add_argument('--quick',action='store_true');p.add_argument('--cpu-only',action='store_true');p.add_argument('--output',default='research/detail-immunity-verification.json');args=p.parse_args()
    d=None if args.cpu_only else Cuda()
    try:rows=sum((verify(d,b,args.quick,args.cpu_only) for b in (('cpu',) if args.cpu_only else ('native','ptx') if args.backend=='both' else (args.backend,))),[])
    finally:
        if d:d.close()
    if args.cpu_only and not args.quick:cpu_assertions(rows)
    files=['scripts/verify-immunity-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/engine_worker.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
    if not args.cpu_only:files+=['app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json']
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(row.get('passed',args.cpu_only) for row in rows),cpu_reference_only=args.cpu_only,
        cpu_trace_used_as_gpu_input=False,cases=rows,scope='Debuff immunity in complete five-member battles, including raw real skills plus authored harmful inputs; not full incoming boss attacks.',
        source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
