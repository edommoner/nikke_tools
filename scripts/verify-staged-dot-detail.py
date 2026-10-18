"""Shared staged clocks: independent quantities and a few whole-squad interactions."""
import argparse,copy,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a,body_for
from gpu_selector import Cuda
from calculator.buff_manager import BuffManager
from staged_dot_runtime import damage_stack
from staged_dot_specs import MODEL_WARNING
from effect_runtime import pool
import detail_gpu as g

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v=load('staged_dot_oracle','scripts/verify-gauge-detail.py');N=v.NAMES;E=v.effect

def definition(count=3,override=1,cap=10):
    parent=E('parent','damage','sequential_damage:'+str(count),100,'target',event='inactive')
    dot=E('phase','damage','dot_damage',100,'same_target:parent',scaling='stack_count',max_stack=cap,tick_interval=.4,duration=2,ramp_interval=.2,post_ramp_tick_delay=.5)
    dot['source']='스킬3'
    if override is not None:dot['ramp_damage_stack']=override
    return parent,dot

def quantities(device,backend):
    cases=[]
    for mode in ('fixed','accumulated','capped','recast','remove','nested'):
        parent,dot=definition(override=None if mode in ('accumulated','capped') else 1,cap=1 if mode=='capped' else 10)
        extra=[E('no critical','buff','crit_rate',-15,'all_allies'),parent,dot]
        actions=[(0,0),(.200001,None),(.400001,None),(.600001,None),(1.100001,None)]
        expected=[0,1000,3000,6000,9000] if mode=='accumulated' else [0,1000,2000,3000,4000] if mode=='capped' else [0,1000,2000,3000,6000]
        if mode=='recast':
            dot['trigger']['timing'].append('burst_cast');actions=[(0,0),(.1,3),(.21,None),(.300001,None),(.700001,None)];expected=[0,0,0,1000,3000]
        if mode=='remove':
            extra.append(E('remove phase','instant','remove_named_buff',0,'target',event='on_attack',target_effect='phase'))
            actions=[(0,0),(.200001,None),(.3,7),(1.2,None)];expected=[0,1000,1000,1000]
        if mode=='nested':
            extra.append(E('once child refresh','instant','force_skill_use',0,event='hit_count:phase:1',target_skill='스킬3',max_trigger=1))
            actions=[(0,0),(.21,None),(.410001,None),(.610001,None)];expected=[0,1000,2000,3000]
        cases.append((mode,extra,actions,expected))
    rows=[];chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in N]
    stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in N}
    for name,extra,actions,expected in cases:
        effects=[(e,N[0]) for e in extra];program=g.compile_effects(chars,effects);definition_row=next(i for i,r in enumerate(program['effects']) if r[340]>0)
        class BM(BuffManager):
            def _register_all(self):self._effects=copy.deepcopy(effects);self._build_notify_index()
            def char_effects(self,name):return [effect for effect,owner in self._effects if owner==name]
        manager=BM(chars,state=dict(base_stats=stats,full_burst=False,enemy=dict(defense=0),hp={n:1000000 for n in N},hp_pct={n:100 for n in N}))
        cpu_total=0
        def damage(effect,caster,t):
            nonlocal cpu_total
            cpu_total+=1000*damage_stack(manager,effect,caster)
            manager.notify('hit_count:'+effect['name'],t,caster)
        manager.register_damage_handler(damage)
        script=[];samples=[];totals=[]
        for at,(t,event) in enumerate(actions):
            if event is not None:
                manager.tick(t);manager.notify({0:'battle_start',3:'burst_cast',7:'on_attack'}[event],t,N[0]);script.append([t,0,event,0,0,-1,0,0])
            manager.tick(t);record=next((r for r in pool(manager,'staged_dot').values() if r.caster==N[0]),None)
            if record:
                sample=[1,record.carrier.stack,record.total,record.index,record.generation,record.next_at if record.index<record.total else -1,manager._dot_timers[id(record.effect)][1],record.carrier.expires_at,1]
            else:sample=[0]*9
            samples.append(sample);totals.append(cpu_total)
            script.append([t,2,130,0,definition_row,len(samples)*2-2,0,0])
            script.append([t,2,0,0,-1,len(samples)*2-1,0,0])
            # The second read-only query ticks once in a non-autonomous script.
            manager.tick(t)
        assert totals==expected,(name,'independent CPU totals',totals,expected)
        result=None if device is None else g.run(device,[program],script,[[0,0]],[stats],module_backend=backend)
        actual=[]
        for i,sample in (enumerate(samples) if result else []):
            query=result['queries'][0][i*2];total=result['queries'][0][i*2+1][38];actual.append(total)
            assert all(math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-8) for x,y in zip(sample,query)),(name,i,sample,query[:9])
        if result:assert actual==expected,(name,'GPU totals',actual,expected)
        rows.append(dict(name='staged-'+name,passed=True,expected_damage=expected,cpu_damage=totals,gpu_damage=actual if result else None,frames=samples,workspace_bytes=result['workspace_bytes'] if result else None))
        print(json.dumps(dict(name=name,passed=True)),flush=True)
    return rows

def squads(device,backend):
    from unittest.mock import patch
    def compare(name,body):
        original_gpu=v.full.evaluate_full;original_cpu=a.evaluate;observed=[]
        def gpu(*args,**kwargs):
            result=original_gpu(*args,**kwargs);assert MODEL_WARNING in result['app_warnings'];observed.append('gpu');return result
        def cpu(request):
            result=original_cpu(request)
            if not request.get('_compile_gpu_detail'):assert MODEL_WARNING in result['app_warnings'];observed.append('cpu')
            return result
        with patch.object(v.full,'evaluate_full',gpu),patch.object(a,'evaluate',cpu):
            result=v.full.compare(device,name,body,module_backend=backend)
        assert set(observed)=={'cpu','gpu'};result['timing_model_warning']=True;return result
    rows=[]
    for name,names in (
        ('raw-staged-dot-burst',['사쿠라 : 블룸 인 서머','리타','크라운','앨리스','모더니아']),
        ('raw-staged-dot-sources-and-counters',['N102','크라운','사쿠라 : 블룸 인 서머','아인','일레그 : 붐 앤 쇼크'])):
        body=body_for(names,45,True);body.update(seed=12345,burst_gauge_mode='fixed')
        if 'counters' in name:body['enemy']['code']='작열'
        row=compare(name,body);assert row['passed'],row
        assert any(e['character']=='사쿠라 : 블룸 인 서머' for e in row['gpu_bursts'])
        rows.append(row);print(json.dumps(dict(name=name,passed=True,cpu=row['cpu_total'],gpu=row['gpu_total'])),flush=True)
    parent,dot=definition('resource');dot['fixed_value']=10
    effects=[E('counter start','instant','gauge_charge',3.8,gauge_id='resource',gauge_max=10),parent,dot,
        E('consume count later','instant','gauge_consume',-1,event='every:0.25s',gauge_id='resource',max_trigger=1),
        E('later attack buff','buff','atk_pct',100,event='every:0.45s',duration=1,max_trigger=1)]
    body=body_for(N,8,True);body.update(seed=12345,burst_gauge_mode='fixed')
    with v.custom_effects({N[0]:effects}):row=compare('staged-frozen-count-live-damage-buffs',body)
    assert row['passed'],row;rows.append(row);print(json.dumps(dict(name=row['name'],passed=True)),flush=True)
    return rows

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('native','ptx'),default='native');parser.add_argument('--cpu-preflight',action='store_true');args=parser.parse_args()
    files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+[ROOT/'app/detail_effects.cu',ROOT/'tests/test_staged_dot_runtime.py',ROOT/'data/engine-effect-overrides.json']
    if not args.cpu_preflight:files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};started=time.perf_counter();device=None if args.cpu_preflight else Cuda()
    try:rows=quantities(device,args.backend)+([] if args.cpu_preflight else squads(device,args.backend))
    finally:
        if device:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=all(r['passed'] for r in rows),cases=rows,source_stable=True,source_sha256=before,cpu_trace_used_as_gpu_input=False,seconds=time.perf_counter()-started,scope='Authored staged applications with generation-safe live damage queries; current aimed-enemy model, not independent game-frame verification.')
    suffix='cpu-preflight' if args.cpu_preflight else args.backend
    (ROOT/f'research/staged-dot-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
