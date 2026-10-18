"""Ally HP gates use effect-owner activation and actual-recipient runtime HP."""
import argparse, hashlib, importlib.util, json, math, random, sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import run, evaluate_full
from detail_coverage import body_for, a
from gpu_service import resolve_verification
from calculator.buff_manager import BuffManager
from gpu_selector import Cuda

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

oracle=load('ally_hp_oracle','scripts/verify-detail.py')
p=load('ally_hp_periodic','scripts/verify-periodic-detail.py')
raw_effects=load('ally_hp_injection','scripts/verify-cleanse-detail.py')
E=p.effect
NAMES=['리타','크라운','앨리스','모더니아','루주']

def whole_battle(device,label,body,extra,backend,drain):
    managers=[];observed=[]
    original_init=BuffManager.__init__;original_condition=BuffManager._condition_ok
    original_runtime=BuffManager._runtime_condition_ok
    def initialize(self,*args,**kwargs):
        original_init(self,*args,**kwargs);managers.append(self)
    def condition(self,conditions,caster,t,eff=None):
        result=original_condition(self,conditions,caster,t,eff)
        if any(c.startswith('ally_hp_below:') for c in conditions):observed.append(result)
        return result
    def runtime(self,conditions,*args,**kwargs):
        result=original_runtime(self,conditions,*args,**kwargs)
        if any(c.startswith('ally_hp_below:') for c in conditions):observed.append(result)
        return result
    with raw_effects.injected_effects(extra),patch.object(BuffManager,'__init__',initialize),patch.object(BuffManager,'_condition_ok',condition),patch.object(BuffManager,'_runtime_condition_ok',runtime):
        compiled=a.evaluate({**body,'_compile_gpu_detail':True})
        gpu=evaluate_full(device,compiled,module_backend=backend)
        managers.clear();observed.clear()
        cpu=a.evaluate(body);final_rng=list(random.getstate()[1]);bm=managers[-1]
        hp={n:dict(hp=bm.state['hp'][n],hp_pct=bm.state['hp_pct'][n],max_hp=bm.effective_max_hp(n)) for n in body['squad']}
    checks=resolve_verification(gpu,cpu)['compute']['cpu_verification'].copy()
    checks['final_random_state']=gpu['_random_state']==final_rng
    checks['final_hp']=all(math.isclose(value,gpu['compute']['final_hp'][n][key],rel_tol=1e-12,abs_tol=1e-7) for n,data in hp.items() for key,value in data.items())
    checks['condition_exercised']=drain in observed
    return dict(name=label,backend=backend,mode=body['burst_gauge_mode'],shooting=body['shooting_policy'],passed=all(checks.values()),checks=checks,cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],cpu_hp=hp,gpu_hp=gpu['compute']['final_hp'],condition_results=sorted(set(observed)))

def cpu_oracle(program,script,enemy,stats):
    # The legacy event oracle predates HP instants; initialize the same HP
    # maps as timeline.simulate before registering the unmodified handlers.
    original=oracle.BuffManager.__init__
    def initialize(self,*args,**kwargs):
        original(self,*args,**kwargs)
        self.state['hp']={n:stats[n]['hp'] for n in self.squad_names}
        self.state['hp_pct']={n:100.0 for n in self.squad_names}
        for name in self.squad_names:self.sync_hp(name)
    with patch.object(oracle.BuffManager,'__init__',initialize):
        return oracle.oracle(program,script,enemy,stats,timeline_handlers=True)

def primitives():
    # Boundary, source/recipient distinction, all five query orders and healing.
    for threshold in (0,30,50,100):
        for hp in (max(0,threshold-.01),threshold,min(100,threshold+.01)):
            effects=[(E('gate','buff','atk_pct',23,'all_allies',event='passive',condition=[f'ally_hp_below:{threshold}']),NAMES[0]),
                     (E('drain','instant','current_hp_reduce',100-hp,NAMES[2],event='burst_cast'),NAMES[1]),
                     (E('heal','instant','heal_hp_pct',100,'all_allies',event='full_burst_start',scaling='max_hp'),NAMES[1])]
            for order in (list(range(5)),list(reversed(range(5)))):
                commands=[(0,0,i) for i in range(5)]+[(.1,3,1)]+[(.2,'query',i) for i in order]+[(.3,1,1)]+[(.4,'query',i) for i in order]
                yield f'hp-{threshold}-{hp}-order{order[0]}',NAMES,effects,commands,None
    # Finite buff: activation must fail while all allies are healthy, and the
    # persistent runtime test must later select the damaged recipient only.
    for timing in ('battle_start','passive','on_attack'):
        effects=[(E('gate','buff','atk_pct',23,'all_allies',event=timing,duration=3,condition=['ally_hp_below:50']),NAMES[0]),
                 (E('drain','instant','current_hp_reduce',50,NAMES[2],event='burst_cast'),NAMES[1])]
        commands=[(0,0,i) for i in range(5)]+[(.05,7,0)]+[(.06,'query',i) for i in range(5)]+[(.1,3,1),(.2,7,0)]+[(.3,'query',i) for i in range(5)]
        yield 'finite-'+timing,NAMES,effects,commands,None
    # Includes a defender who is the caster: "ally" excludes that caster.
    for names in (NAMES,['리타','도라','앨리스','모더니아','루주'],['크라운','리타','앨리스','모더니아','루주']):
        for condition in ('has_defender_ally','no_defender_ally'):
            from calculator.buff_manager import _NIKKE
            has=any(_NIKKE.get(n,{}).get('class')=='방어형' for n in names[1:])
            expected=[23 if has==(condition=='has_defender_ally') else 0]*5
            effects=[(E('defender gate','buff','atk_pct',23,'all_allies',condition=[condition]),names[0])]
            commands=[(0,0,i) for i in range(5)]+[(.1,'query',i) for i in range(5)]
            yield condition+'-'+names[0]+'-'+names[1],names,effects,commands,expected

def verify(device,backend,quick=False):
    rows=[]
    for name,names,effects,commands,expected in primitives():
        program=oracle.program(oracle.characters(names),effects)
        bs={n:{'atk':100000+i*1234,'hp':1000000,'def':1000} for i,n in enumerate(names)}
        script=[];index=0
        for t,event,who in commands:
            script.append([t,2 if event=='query' else 0,0 if event=='query' else event,who,-1,index if event=='query' else -1,0,0])
            if event=='query':index+=1
        cpu,_=cpu_oracle(program,script,[31784,50],bs)
        gpu=run(device,[program],script,[[31784,50]],[bs],module_backend=backend)['queries'][0]
        errors=[]
        for i,(x,y) in enumerate(zip(cpu,gpu)):
            for k in range(32):
                if not math.isclose(x[k],y[k],abs_tol=1e-9,rel_tol=1e-12):errors.append([i,k,x[k],y[k]])
            if expected is not None and (x[0]!=expected[i] or y[0]!=expected[i]):errors.append([i,'positive-control',expected[i],x[0],y[0]])
        assert len(cpu)==len(gpu)==index
        row=dict(name=name,backend=backend,passed=not errors,errors=errors,cpu_atk=[q[0] for q in cpu],gpu_atk=[q[0] for q in gpu])
        rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
    if not quick:
        for raw in (False,True):
            names=['트리나','리타','크라운','앨리스','모더니아'] if raw else NAMES
            for drain in (False,True):
                for shooting in ('auto','character'):
                    for mode in ('fixed','accumulate'):
                        body=body_for(names,20,True)
                        body.update(seed=12345,shooting_policy=shooting,burst_policy='rules',burst_gauge_mode=mode,_debug_random_state=True)
                        extra={names[1]:[E('verification drain','instant','current_hp_reduce',35,names[3],event='every:2s')] if drain else []}
                        if not raw:extra[names[0]]=[E('verification gate','buff','atk_pct',23,'all_allies',event='passive',condition=['ally_hp_below:50'])]
                        row=whole_battle(device,f'whole-raw{raw}-drain{drain}-{shooting}',body,extra,backend,drain)
                        rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
    return rows

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx','both'],default='both');ap.add_argument('--quick',action='store_true');ap.add_argument('--output',default='research/detail-ally-conditions-verification.json');args=ap.parse_args()
    files=['scripts/verify-ally-conditions-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    device=Cuda()
    try:rows=[row for backend in (('native','ptx') if args.backend=='both' else (args.backend,)) for row in verify(device,backend,args.quick)]
    finally:device.close()
    assert hashes=={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},'Sources changed during verification'
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=bool(rows) and all(r['passed'] for r in rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False,objective_complete=False)
    (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if report['passed'] else 1)
