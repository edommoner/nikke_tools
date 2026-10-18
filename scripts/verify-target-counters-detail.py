"""Shared target-counter quantities and real autonomous landing integration."""
import argparse,copy,hashlib,importlib.util,json,math,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a,body_for
from gpu_selector import Cuda
from calculator.buff_manager import BuffManager
from effect_runtime import state,pool
from impact_specs import ActorHandle,Impact,impact_command
from target_counter_cases import clone_cases,marker
from resource_frame_capture import FrameCapture
import detail_gpu as g

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
v=load('counter_gauge_oracle','scripts/verify-gauge-detail.py')
cpu=load('counter_cpu_table','tests/test_target_counter_runtime.py')

def quantities(device,backend):
    rows=[];names=v.NAMES
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in names]
    stats={n:dict(atk=1000,hp=10000,**{'def':100}) for n in names}
    for case in clone_cases():
        program=g.compile_effects(chars,[(e,names[0]) for e in case['effects']]);script=[]
        for at,(t,action) in enumerate(case['actions']):
            kind,*args=action
            if kind in ('activate','refresh'):script.append([t,0,0 if kind=='activate' else 7,0,0,-1,0,0])
            elif kind=='hit':
                family,outcome,target_kind,identity,generation,credit,damage,*who=args
                script.append(impact_command(t,Impact(names[who[0] if who else 2],ActorHandle(target_kind,identity,generation),family,outcome,damage,credit),names))
            else:script.append([t,9,args[0],0,args[1],args[2],0,0])
            script.append([t,2,127,0,-1,at,0,0])
        result=g.run(device,[program],script,[[0,0]],[stats],module_backend=backend)
        observed=[(int(r[0]),r[1],int(r[2]),int(r[5])) for r in result['queries'][0]]
        assert observed==case['expected'],(case['name'],observed,case['expected'])
        bm,completed=cpu.exercise(case)
        for (_,action),query in zip(case['actions'],result['queries'][0]):
            assert query[3]==0,'No completed old epoch may remain as a live marker after callbacks'
        if completed:
            last=completed[-1];q=result['queries'][0][-1]
            assert q[8]>0 and q[9]==last.epoch and q[10]==0 and q[11]==program['states'][last.name]
            assert q[12:17]==[int(last.actor.kind),last.actor.identity,last.actor.generation,last.credit,int(last.reason=='death')]
        rows.append(dict(name=case['name'],passed=True,quantities=observed,completions=len(completed),last_epoch=completed[-1].epoch if completed else None))
        print(json.dumps(dict(name=case['name'],passed=True)),flush=True)
    effects=[(marker(threshold=1),names[0]),(marker(threshold=1),names[1])]
    program=g.compile_effects(chars,effects)
    script=[[0,0,0,owner,0,-1,0,0] for owner in (0,1)]+[impact_command(.1,Impact(names[2],ActorHandle(0,0,1),0,2,13),names),[.1,2,127,0,-1,0,0,0],[.1,2,127,1,-1,1,0,0]]
    result=g.run(device,[program],script,[[0,0]],[stats],module_backend=backend)
    assert all(row[0]==0 and row[2]==2 and row[5]==2 and row[10]==1 for row in result['queries'][0])
    rows.append(dict(name='same-marker-name-is-private-to-each-owner',passed=True,completions=2))
    E=v.effect;counter=marker('capture',1)
    effects=[counter,E('no critical','buff','crit_rate',-15),
        E('overflow before increment','damage','damage',100,'target',event='event:target_counter_complete:capture',condition=['gauge_eq:fuel:2']),
        E('capture increment','instant','gauge_charge',1,event='event:target_counter_complete:capture',gauge_id='fuel',gauge_max=2)]
    program=g.compile_effects(chars,[(e,names[0]) for e in effects]);script=[[0,0,0,0,0,-1,0,0]]
    for i,t in enumerate((.1,.2,.3)):
        if i:script.append([t,0,7,0,0,-1,0,0])
        script.extend([impact_command(t,Impact(names[2],ActorHandle(0,0,1),0,2,13),names),[t,5,0,0,0,-1,0,0],[t,2,127,0,-1,2*i,0,0],[t,2,102,0,program['states']['fuel'],2*i+1,0,0]])
    result=g.run(device,[program],script,[[0,0]],[stats],module_backend=backend)
    assert [r[0] for r in result['queries'][0][1::2]]==[1,2,2]
    assert result['totals'][0]==[1000,0,0,0,0],result['totals']
    assert result['queries'][0][-2][2]==3
    rows.append(dict(name='capacity-is-checked-before-capture-increment',passed=True,damage=1000,captures=3))
    effects=[marker('weapon counter',1,families=['weapon']),marker('skill counter',1,families=['skill']),
        E('no critical','buff','crit_rate',-15),
        E('counter-generated attack','damage','damage',100,'target',event='event:target_counter_complete:weapon counter'),
        E('child landing witness','instant','gauge_charge',1,event='event:target_counter_complete:skill counter',gauge_id='child')]
    program=g.compile_effects(chars,[(e,names[0]) for e in effects])
    script=[[0,0,0,0,0,-1,0,0],impact_command(.1,Impact(names[2],ActorHandle(0,0,1),0,2,13),names),
        [.1,2,127,0,-1,0,0,0],[.1,5,0,0,0,-1,0,0],[.1,2,127,0,-1,1,0,0],[.1,2,102,0,program['states']['child'],2,0,0]]
    result=g.run(device,[program],script,[[0,0]],[stats],module_backend=backend);q=result['queries'][0]
    assert q[0][0]==1 and q[0][2]==1 and q[1][0]==0 and q[1][2]==2 and q[2][0]==1 and result['totals'][0][0]==1000,(q,result['totals'])
    rows.append(dict(name='counter-generated-skill-landing-reaches-other-counter',passed=True,completions=2,child_resource=1,damage=1000))
    return rows

def scenarios():
    E=v.effect
    name='body progress';m=marker(name,30);m['trigger']['timing']=['battle_start','every:0.5s']
    effects={v.NAMES[0]:[m,E('completion ATK','buff','atk_pct',15,'all_allies',event='event:target_counter_complete:'+name,duration=.4),
        E('completion resource','instant','gauge_charge',1,event='event:target_counter_complete:'+name,gauge_id='captures',gauge_max=100),
        E('retirement crit','buff','crit_dmg',7,'all_allies',event='event:state_end:'+name,duration=.2),
        E('counted periodic damage','damage','dot_damage',25,'target',tick_interval=.2,duration=8)]}
    body=body_for(v.NAMES,8,True);body.update(seed=12345,burst_gauge_mode='fixed',_debug_impact_frames=True,_debug_target_counter_frames={'who':0})
    yield 'autonomous-body-hits-refresh-and-effect-order',body,effects
    names=['슈가']+v.NAMES[:4];name='part progress'
    m=marker(name,1000000000,actor=dict(kind='part',identity=0,generation=1));m['trigger']['timing']=['battle_start']
    effects={names[0]:[m,E('piercing weapons','buff','pierce_enabled',1,'all_allies'),
        E('drain','instant','current_hp_reduce',50,'all_allies'),E('landed recovery','buff','lifesteal_pct',25,'all_allies'),
        E('death ATK','buff','atk_pct',25,'all_allies',event='event:target_counter_complete:'+name,duration=5),
        E('death before landed healing','buff','heal_received_pct',50,'all_allies',event='event:target_counter_complete:'+name,duration=3)]}
    body=body_for(names,8,True);body.update(seed=12345,burst_gauge_mode='fixed',_debug_impact_frames=True,_debug_target_counter_frames={'who':0})
    body['enemy']['parts']=[dict(name='fragile',hp=100000,reach=1),dict(name='solid',hp=0,reach=1)]
    yield 'autonomous-part-death-before-lifesteal',body,effects

def raw_scenarios():
    owner='일레그 : 붐 앤 쇼크'
    body=body_for(['N102','크라운','앨리스','모더니아',owner],90,True)
    body['enemy']['code']='작열'
    body.update(seed=12345,burst_gauge_mode='fixed',_debug_target_counter_frames={'who':4})
    yield 'raw-capture-to-cap-and-overflow',body,{}
    body=body_for(['N102','크라운',owner,'앨리스','모더니아'],8,True)
    body['enemy']['code']='작열'
    body.update(seed=12345,burst_gauge_mode='fixed',_debug_target_counter_frames={'who':2})
    yield 'raw-in-burst-six-hit-consumption-floor',body,{}
    yield 'raw-in-burst-thirteen-hit-at-initial-cap',body,{owner:[v.effect('authored initial resource','instant','gauge_charge',13,gauge_id='유령',gauge_max=13)]}

def additive_effects(extra):
    from contextlib import contextmanager
    @contextmanager
    def apply():
        original=BuffManager.char_effects
        def effects(manager,name):return original(manager,name)+copy.deepcopy(extra.get(name,[]))
        with patch.object(BuffManager,'char_effects',effects):yield
    return apply()

def squads(device,backend,cpu_only=False):
    rows=[]
    for name,body,effects in list(scenarios())+list(raw_scenarios()):
        from calculator.timeline import CharState
        original=BuffManager.__init__;owner=body['squad'][body['_debug_target_counter_frames']['who']];captures=[];overflows=[];bursts=[]
        original_dispatch=BuffManager._dispatch_instant;original_register=BuffManager.register_damage_handler;original_get=BuffManager.get_buffs;element_before=[];element_after=[]
        original_element=CharState.element_match;element_matches=False
        def element_match(character,manager):
            nonlocal element_matches
            value=original_element(character,manager)
            if name.startswith('raw-') and character.name==owner:element_matches|=bool(value)
            return value
        def get_buffs(manager,caster,*args,**kwargs):
            result=original_get(manager,caster,*args,**kwargs)
            if name.startswith('raw-') and caster==owner and 'hp' in manager.state:
                count=manager.state.get('gauges',{}).get(owner,{}).get('유령',0)
                (element_after if count>=4 else element_before).append(result.get('element_bonus_pct',0))
            return result
        def dispatch(manager,effect,caster,t,*args,**kwargs):
            watched=name.startswith('raw-') and caster==owner and effect.get('name')=='유령 포획'
            before=manager.state.get('gauges',{}).get(owner,{}).get('유령',0)
            result=original_dispatch(manager,effect,caster,t,*args,**kwargs)
            if watched:captures.append(dict(time=t,before=before,after=manager.state['gauges'][owner]['유령']))
            return result
        def register(manager,callback):
            def damage(effect,caster,t):
                if name.startswith('raw-') and caster==owner:
                    value=manager.state.get('gauges',{}).get(owner,{}).get('유령',0)
                    if effect.get('name')=='고스트 버스터 2':overflows.append(dict(time=t,resource=value,capture_number=len(captures)+1))
                    if effect.get('name') in ('13 고스트','13 고스트 3'):bursts.append(dict(time=t,resource=value,effect=effect['name']))
                return callback(effect,caster,t)
            return original_register(manager,damage)
        def initialize(manager,*args,**kwargs):
            original(manager,*args,**kwargs)
            if 'hp' in manager.state:state(manager).counter_trace=[]
        def project(manager,t,witness):
            runtime=state(manager);records=[r for r in pool(manager,'target_hit_counter').values() if r.caster==owner and r.expires>t and any(ab is r.carrier for ab in manager._active)]
            last=None
            if runtime.counter_last:
                at,c=runtime.counter_last;last=dict(epoch=c.epoch,owner=c.owner,name=c.name,actor=[int(c.actor.kind),c.actor.identity,c.actor.generation],credit=c.credit,reason=c.reason,time=at)
            return [dict(time=t,active=len(records),credit=sum(r.credit for r in records),completed=runtime.counter_completed,latched=sum(r.done for r in records),dead_actors=len(runtime.dead_actors),epoch=runtime.counter_epoch,last=last)]
        with (additive_effects(effects) if name.startswith('raw-') else v.custom_effects(effects)),patch.object(BuffManager,'__init__',initialize),patch.object(BuffManager,'_dispatch_instant',dispatch),patch.object(BuffManager,'register_damage_handler',register),patch.object(BuffManager,'get_buffs',get_buffs),patch.object(CharState,'element_match',element_match),FrameCapture(v.full,project) as witness:
            from calculator import timeline
            code=timeline.simulate.__code__;previous=sys.gettrace()
            def trace(frame,event,arg):return trace if frame.f_code is code else None
            try:
                sys.settrace(trace)
                if cpu_only:
                    result=a.evaluate(body);row=dict(name=name,passed=True,cpu_total=result['total_damage'])
                else:row=v.full.compare(device,name,body,module_backend=backend)
            finally:sys.settrace(previous)
        samples=witness.samples+witness.final_samples
        assert samples and samples[-1]['completed']>0,(name,samples[-1:])
        assert samples[-1]['last']['reason']==('death' if 'part-death' in name else 'threshold')
        if name.startswith('raw-'):
            assert captures and all(c['after']==min(13,c['before']+1) for c in captures),captures
            if name=='raw-capture-to-cap-and-overflow':
                assert not bursts and len(captures)>=14 and overflows and overflows[0]['capture_number']==14,(len(captures),overflows,bursts)
                assert element_before and element_after and max(element_after)>=min(element_before)+30.23-1e-9,(element_before[:3],element_after[:3])
                assert element_matches
            if name=='raw-in-burst-six-hit-consumption-floor':assert any(b['effect']=='13 고스트' for b in bursts),bursts
            if name=='raw-in-burst-thirteen-hit-at-initial-cap':assert any(b['effect']=='13 고스트 3' for b in bursts) and overflows,bursts
        if not cpu_only:
            observed=copy.deepcopy(witness.gpu['_target_counter_frames'])
            assert len(samples)==len(observed)
            def close(left,right):
                if isinstance(left,dict):return left.keys()==right.keys() and all(close(left[k],right[k]) for k in left)
                if isinstance(left,(float,int)):return math.isclose(left,right,rel_tol=1e-12,abs_tol=1e-6)
                return left==right
            for right in observed:
                if right['last']:right['last'].pop('uid') # Opaque allocation IDs differ across independent runtimes.
            for i,(left,right) in enumerate(zip(samples,observed)):assert close(left,right),(name,i,left,right)
            assert row['passed'],row
        row.update(counter_frames=len(samples),completed=samples[-1]['completed'],counter_final=samples[-1])
        if name.startswith('raw-'):row.update(captures=captures,overflows=overflows,cast_effects=bursts,single_body_model=True,enemy_code=body['enemy']['code'],element_matches_enemy=element_matches,element_bonus_below_four=min(element_before) if element_before else None,element_bonus_at_least_four=max(element_after) if element_after else None)
        rows.append(row)
        print(json.dumps(dict(name=name,passed=True,frames=len(samples),completed=samples[-1]['completed'])),flush=True)
    return rows

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('native','ptx'),default='native');parser.add_argument('--cpu-preflight',action='store_true');args=parser.parse_args()
    files=sorted({str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'app').glob('*.py')}|{'app/detail_effects.cu','data/engine-effect-overrides.json','scripts/verify-target-counters-detail.py','scripts/target_counter_cases.py','scripts/resource_frame_capture.py','scripts/verify-gauge-detail.py','scripts/verify-extended-detail.py','tests/test_target_counter_runtime.py'})
    if not args.cpu_preflight:files+=['app/detail_effects-sm86.cubin','app/detail_effects-sm86.json'] if args.backend=='native' else ['app/detail_effects.ptx','app/detail_effects-build.json']
    def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
    before=hashes();device=None if args.cpu_preflight else Cuda()
    try:rows=([] if args.cpu_preflight else quantities(device,args.backend))+squads(device,args.backend,args.cpu_preflight)
    finally:
        if device:device.close()
    assert before==hashes()
    report=dict(passed=all(r['passed'] for r in rows),cases=rows,source_stable=True,source_sha256=before,cpu_trace_used_as_gpu_input=False,
        scope='Explicit physical-actor credit policies, shared completion lifecycle and bounded single-body raw capture model. Component and blocked-hit raw capture behavior is not admitted or claimed game-verified.')
    suffix='cpu-preflight' if args.cpu_preflight else args.backend
    (ROOT/f'research/target-counters-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
