"""Shared clocks: authored quantities, independent CPU runs and raw squad inputs."""
import argparse,copy,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a,body_for
from gpu_selector import Cuda
from calculator.buff_manager import BuffManager
from periodic_source_runtime import refresh,tick,count
from effect_runtime import pool
from periodic_source_specs import LEGACY_WARNING
import detail_gpu as g

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
v=load('periodic_source_oracle','scripts/verify-gauge-detail.py')
N=v.NAMES
def source(name,slots,base,step=0,event='battle_start',legacy=False):
    e=dict(name='refresh '+name+' '+event,source='스킬1',type='instant',stat='feather_refresh' if legacy else 'periodic_source_refresh',target='self',trigger=dict(timing=[event],condition=[]))
    if legacy:e.update(feather_id=name,feather_slots=slots,feather_interval_base=base,feather_interval_step_pct=step)
    else:e['periodic_source']=dict(name=name,slots=slots,base_interval=base,population_reduction_pct=step)
    return e

def quantities(device,backend):
    plans=[
        ('expiry-keeps-reservation',[(source('A',[-1,2,3],1,10),0)],[(0,0),(0.8,None),(1.6,None),(2.400001,None),(3.300001,None)],[(3,.8,1),(3,1.6,1),(3,2.4,1),(2,3.3,1),(1,4.3,1)]),
        ('atomic-refresh-before-old-due',[(source('A',[-1],1),0),(source('A',[-1,2],2,event='burst_cast'),0)],[(0,0),(.9,3),(1,None),(2.9,None)],[(1,1,1),(2,2.9,2),(2,2.9,2),(1,4.9,2)]),
        ('nested-refresh-survives-parent-commit',[(source('A',[-1],1),0),(source('A',[-1],3,event='source_tick:A'),0)],[(0,0),(1,None),(2,None),(4,None)],[(1,1,1),(1,4,2),(1,4,2),(1,7,3)]),
        ('expired-zero-stops-clock',[(source('A',[1],1),0),(v.effect('A','buff','crit_dmg',0),0),(v.effect('empty source damage','damage','armor_break_damage:A',100,event='on_attack'),0)],[(0,0),(1,None),(2,7)],[(1,1,1),(0,-1,1),(0,-1,1)]),
        ('legacy-data-adapter',[(source('A',[-1,2],1,10,legacy=True),0)],[(0,0),(.9,None),(1.8,None),(2.700001,None)],[(2,.9,1),(2,1.8,1),(2,2.7,1),(1,3.7,1)]),
        ('source-and-slot-capacity-bound',[(source('A' if i==0 else 'channel'+str(i),[-1]*32,1),0) for i in range(64)],[(0,0),(1,None)],[(32,1,1),(32,2,1)]),
    ]
    rows=[];chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in N]
    stats={n:dict(atk=100000,hp=1000000,**{'def':1000}) for n in N}
    for name,definitions,actions,expected in plans:
        effects=[(e,N[owner]) for e,owner in definitions];program=g.compile_effects(chars,effects)
        class BM(BuffManager):
            def _register_all(self):self._effects=copy.deepcopy(effects);self._build_notify_index()
        manager=BM(chars,state=dict(base_stats=stats,enemy=dict(defense=0),full_burst=False,hp={n:1000000 for n in N},hp_pct={n:100 for n in N}))
        for stat in ('feather_refresh','periodic_source_refresh'):
            manager.register_instant_handler(stat,lambda e,c,t,value:refresh(manager,e,c,t,value))
        script=[];observed=[]
        for t,event in actions:
            if event is not None:
                manager.tick(t);manager.notify({0:'battle_start',3:'burst_cast',7:'on_attack'}[event],t,N[0]);script.append([t,0,event,0,0,-1,0,0])
            manager.tick(t);record=pool(manager,'periodic_sources')[N[0],'A']
            observed.append((record.count(t),-1 if record.next_at is None else record.next_at,record.epoch))
            script.append([t,2,129,0,program['states']['A'],len(observed)-1,0,0])
        result=None if device is None else g.run(device,[program],script,[[0,0]],[stats],module_backend=backend)
        gpu=None if result is None else [(q[1],q[2],q[3]) for q in result['queries'][0]]
        close=lambda left,right:all(math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-9) for a,b in zip(left,right) for x,y in zip(a,b))
        assert close(expected,observed),(name,'CPU',expected,observed)
        if result is not None:assert close(expected,gpu),(name,'GPU',expected,gpu)
        if result is not None and name=='expired-zero-stops-clock':assert not any(result['totals'][0]),'A present empty source must not fall back to a same-named buff stack'
        if result is not None and name=='source-and-slot-capacity-bound':assert all(q[5]==64 for q in result['queries'][0])
        row=dict(name=name,passed=True,expected=expected,cpu=observed,gpu=gpu,workspace_bytes=result['workspace_bytes'] if result else None);rows.append(row)
        print(json.dumps(dict(name=name,passed=True)),flush=True)
    return rows

def squads(device,backend):
    from unittest.mock import patch
    rows=[]
    for variant in ('offburst','reordered-burst','counter-combination'):
        offburst=variant=='offburst'
        names=['N102','크라운','앨리스','모더니아','아인'] if offburst else ['크라운','아인','리타','모더니아','앨리스']
        if variant=='counter-combination':names=['N102','크라운','아인','모더니아','일레그 : 붐 앤 쇼크']
        body=body_for(names,45,True);body.update(seed=12345,burst_gauge_mode='fixed')
        if variant=='counter-combination':body['enemy']['code']='작열'
        # Check displayed provenance on a real result, independent of damage parity.
        compiled=a.evaluate({**body,'_compile_gpu_detail':True});gpu=g.evaluate_full(device,compiled,module_backend=backend)
        original=a.evaluate;observed=[]
        def evaluate(request):
            result=original(request)
            if not request.get('_compile_gpu_detail'):observed.append(LEGACY_WARNING in result['app_warnings'])
            return result
        with patch.object(a,'evaluate',evaluate):
            row=v.full.compare(device,'raw-periodic-source-'+variant,body,module_backend=backend,gpu_result=gpu)
        assert LEGACY_WARNING in gpu['app_warnings'] and observed and all(observed)
        used=any(b.get('character')=='아인' for b in gpu['burst_timeline'])
        assert used!=offburst,(offburst,gpu['burst_timeline'])
        assert row['passed'],row
        row['estimated_parameters_warning']=True;rows.append(row);print(json.dumps(dict(name=row['name'],passed=True)),flush=True)
    return rows

def combined_source_squad(device,backend):
    effects=[source('shared',[-1,.8],.4,25),source('legacy',[-1],.7,legacy=True),
        v.effect('scoped source witness','buff','atk_pct',3,event='source_tick:shared',max_stack=100),
        v.effect('legacy witness','buff','crit_dmg',2,event='feather_tick',max_stack=100),
        v.effect('source attack','damage','armor_break_damage:shared',10,event='source_tick:shared'),
        v.effect('source child dot','damage','dot_damage',3,'target',event='source_tick:shared',tick_interval=.1,duration=.25),
        source('shared',[-1,.5,.9],.4,25,event='burst_cast')]
    body=body_for(N,8,True);body.update(seed=12345,burst_gauge_mode='fixed')
    with v.custom_effects({N[0]:effects}):
        row=v.full.compare(device,'scoped-and-legacy-channels-with-child-dot',body,module_backend=backend)
    assert row['passed'],row
    print(json.dumps(dict(name=row['name'],passed=True)),flush=True)
    return row

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('native','ptx'),default='native');parser.add_argument('--cpu-preflight',action='store_true');args=parser.parse_args()
    files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+[ROOT/'tests/test_periodic_source_runtime.py',ROOT/'app/detail_effects.cu',ROOT/'data/engine-effect-overrides.json']
    if not args.cpu_preflight:files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};started=time.perf_counter();device=None if args.cpu_preflight else Cuda()
    try:rows=quantities(device,args.backend)+([] if args.cpu_preflight else [combined_source_squad(device,args.backend)]+squads(device,args.backend))
    finally:
        if device:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=all(r['passed'] for r in rows),cases=rows,source_stable=True,source_sha256=before,seconds=time.perf_counter()-started,cpu_trace_used_as_gpu_input=False,
        scope='Authored slot expiry and population clocks; legacy data parameters are estimates, not measured game constants.')
    suffix='cpu-preflight' if args.cpu_preflight else args.backend
    (ROOT/f'research/periodic-sources-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
