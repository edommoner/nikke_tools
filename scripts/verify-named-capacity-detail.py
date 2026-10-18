"""All 256-bit duration-mask boundaries against independent CPU state/combat."""
import argparse,copy,hashlib,importlib.util,json,math,random,sys
from contextlib import nullcontext
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v=load('named_capacity_oracle','scripts/verify-named-detail.py')
t=load('named_capacity_team','scripts/verify-team-hits-detail.py')
ctrl=load('named_capacity_control','scripts/verify-control-detail.py')
import detail_gpu as g
from gpu_selector import Cuda
from gpu_service import resolve_verification
E=v.effect
def primitives():
    for desired in (31,32,63,64,95,96,127,128,159,160,191,192,223,224,254,255):
        for amount in (1,-.75):
            es=[E('padding '+str(i),'buff','crit_dmg',0,event='inactive') for i in range(desired-2)]
            es[0]['trigger']['condition']=['gauge_above:unregistered0:1','gauge_above:unregistered1:1']
            es += [E('mode','buff','atk_pct',10,duration=1),E('padding 1','buff','atk_pct',40,duration=1),E('padding 0','instant','named_buff_duration_extend',amount,event='burst_cast',target_effect='mode')]
            p=v.oracle.program(v.oracle.characters(v.NAMES),[(e,v.NAMES[0]) for e in es])
            assert p['states']['mode']==desired and len(p['states'])<=g.NE and len(p['effects'])<=g.NE
            mask=p['effects'][-1][g.EXTEND_MASK:g.EXTEND_MASK+g.MASK_WORDS]
            assert sum(int(word).bit_count() for word in mask)==1
            assert int(mask[desired//32])&(1<<(desired%32))
            script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+[[.49,2,0,0,-1,0,0,0],[.5,0,3,0,0,-1,0,0],[1.1,2,0,0,-1,1,0,0],[2,2,0,0,-1,2,0,0]]
            yield 'extension-id-'+str(desired)+'-'+str(amount),p,script,[50,10 if amount>0 else 0,0]
def verify_primitives(device,backend):
    rows=[];stats={n:{'atk':100000,'def':20000,'hp':1000000} for n in v.NAMES}
    for name,p,script,expected in primitives():
        cpu,totals=v.oracle.oracle(p,script,[31784,0],stats)
        gpu=g.run(device,[p],script,[[31784,0]],[stats],module_backend=backend)
        checks=dict(queries=all(math.isclose(x[k],y[k],rel_tol=1e-12,abs_tol=1e-8) for x,y in zip(cpu,gpu['queries'][0]) for k in list(range(32))+[36]),totals=totals==gpu['totals'][0],expected_atk=[x[0] for x in cpu]==[x[0] for x in gpu['queries'][0]]==expected)
        row=dict(name=name,backend=backend,kind='primitive',effects=len(p['effects']),states=len(p['states']),checks=checks,passed=all(checks.values()),cpu_atk=[x[0] for x in cpu],gpu_atk=[x[0] for x in gpu['queries'][0]])
        rows.append(row);print(json.dumps(row),flush=True)
    return rows
def battles(long=False):
    names=t.p.NAMES
    for kind in (() if long else ('buff','dot')):
        for amount in (2,-.75):
            body=t.body_for(names,180 if long else 12,True)
            body.update(seed=12345,burst_policy='auto',shooting_policy='character',burst_gauge_mode='accumulate',_debug_random_state=True)
            padding=[E('battle padding '+str(i),'buff','crit_dmg',0,event='inactive') for i in range(129)]
            target='self' if kind=='buff' else 'target'
            subject=E('high '+kind,'buff' if kind=='buff' else 'damage','atk_pct' if kind=='buff' else 'dot_damage',90 if kind=='buff' else 100,target,duration=1,**({} if kind=='buff' else {'tick_interval':.25}))
            extension=E('high extension','instant','named_buff_duration_extend',amount,target,event='every:0.5s',max_trigger=1,target_effect='high '+kind)
            yield kind+'-'+str(amount),body,{names[0]:padding+[subject,extension]}
    for operation in ('tap','hold'):
        names=['리타','크러스트','크라운','앨리스','모더니아']
        body=t.body_for(names,180 if long else 35,True)
        body.update(seed=12345,burst_policy='auto',shooting_policy='character',burst_gauge_mode='accumulate',_debug_random_state=True)
        body['_named_controls']={'크러스트':{'tap_fire':{'rate':3.6,'release':.03,'full_charge_interval':5.5}} if operation=='tap' else {'sequence':[{'t':start,'action':'hold','until':start+3.3} for start in (0,4,8)]}}
        padding=[E('battle padding '+str(i),'buff','crit_dmg',0,event='inactive') for i in range(129)]
        yield 'real-Crust-'+operation,body,{names[0]:padding}
def verify_battles(device,backend,long=False):
    from calculator.buff_manager import BuffManager
    from unittest.mock import patch
    rows=[]
    for name,body,extra in battles(long):
        configured=body.pop('_named_controls',None)
        calls=[];dots=[];dispatch=BuffManager._dispatch_instant;register=BuffManager.register_damage_handler
        def observe(self,eff,caster,t,*args,**kw):
            if eff.get('stat')=='named_buff_duration_extend':calls.append(t)
            return dispatch(self,eff,caster,t,*args,**kw)
        def hook(self,handler):
            def damage(eff,caster,t,*args,**kw):
                if eff.get('name')=='high dot':dots.append(t)
                return handler(eff,caster,t,*args,**kw)
            return register(self,damage)
        with t.raw.injected_effects(extra),ctrl.configured(configured) if configured is not None else nullcontext():
            compiled=t.a.evaluate({**body,'_compile_gpu_detail':True})
            state=compiled['program']['states']['마이야르' if name.startswith('real-') else 'high '+name.split('-')[0]]
            assert state>=128
            gpu=g.evaluate_full(device,compiled,module_backend=backend)
            with patch.object(BuffManager,'_dispatch_instant',observe),patch.object(BuffManager,'register_damage_handler',hook):cpu=t.a.evaluate(body)
            rng=list(random.getstate()[1])
        result=resolve_verification(gpu,cpu);checks=result['compute']['cpu_verification'].copy()
        checks.update(actual_gpu=result['compute']['backend']=='cuda_detail',final_random_state=rng==gpu['_random_state'],extension_exercised=bool(calls))
        if name.startswith('dot'):checks['dot_lifetime_exercised']=len(dots)==(12 if name.endswith('2') else 2)
        row=dict(name=name,backend=backend,kind='battle',duration=body['duration'],state_index=state,effects=len(compiled['program']['effects']),checks=checks,passed=all(checks.values()),cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],extension_times=calls,dot_times=dots,raw_skills_retained=True,padding_effects=129)
        rows.append(row);print(json.dumps(row),flush=True)
    return rows
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx','both'],default='both');ap.add_argument('--long',action='store_true');ap.add_argument('--output',default='research/detail-named-capacity-verification.json');args=ap.parse_args()
    files=['scripts/verify-named-capacity-detail.py','scripts/verify-named-detail.py','scripts/verify-team-hits-detail.py','scripts/verify-control-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    device=Cuda()
    try:rows=[r for b in (('native','ptx') if args.backend=='both' else (args.backend,)) for r in ([] if args.long else verify_primitives(device,b))+verify_battles(device,b,args.long)]
    finally:device.close()
    assert hashes=={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=bool(rows) and all(r['passed'] for r in rows),objective_complete=False,cases=rows,cpu_trace_used_as_gpu_input=False,source_sha256=hashes)
    (ROOT/args.output).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
