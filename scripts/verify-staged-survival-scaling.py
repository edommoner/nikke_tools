"""Whole-squad lost-HP/cover-revival GPU parity; no CPU replay in GPU inputs."""
import argparse,ast,copy,hashlib,importlib.util,inspect,json,math,random,sys,textwrap
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
g=load('scaling_stage_loader','scripts/staged-survival-scaling-runtime.py').install()
s=load('scaling_survival_oracle','scripts/verify-survival-detail.py');N=s.N;B=s.B;E=s.E
from calculator.buff_manager import BuffManager

def body(duration=1,raw=False,names=None,scalar=None):
    b=s.v.body(duration,raw,names);b.update(_debug_hp_events=True)
    if scalar is not None:b['_debug_scalar_query']={'who':scalar,'key':0}
    b['enemy']['patterns']=[s.lethal(at=100)]
    return b

def fixtures():
    for variant in ('full-health','half-health','heal-rearms-value','stacks-do-not-multiply','receiver-health-does-not-scale','max-HP-denominator','source-down-buff-remains','source-revives','stacks-with-bullets','finite-runtime-gate','scaled-maximum','scaled-maximum-revival','stacked-HP-gain'):
        name='lost-'+variant;b=body(1,scalar=1);extra={n:[] for n in N};kw={}
        if variant in ('stacks-do-not-multiply','stacks-with-bullets','stacked-HP-gain'):kw.update(event='every:0.05s',max_stack=3)
        if variant=='stacks-with-bullets':kw['duration_bullets']=20
        if variant=='finite-runtime-gate':kw.update(event='passive',duration=.1)
        e=B('lost HP power','max_hp_pct' if variant=='stacked-HP-gain' else 'max_hp_only_pct' if variant.startswith('scaled-maximum') else 'atk_pct',1.5,N[0] if variant.startswith('scaled-maximum') or variant=='stacked-HP-gain' else N[1],scaling='lost_hp_pct',**kw)
        if variant=='finite-runtime-gate':e['trigger']['condition']=['self_hp_below:60']
        extra[N[0]].append(e)
        if variant in ('half-health','heal-rearms-value','stacks-do-not-multiply','receiver-health-does-not-scale','stacks-with-bullets','finite-runtime-gate','scaled-maximum','stacked-HP-gain'):
            owner=N[1] if variant=='receiver-health-does-not-scale' else N[0];extra[owner].append(E('reduce health','instant','current_hp_reduce',50,event='every:0.2s',max_trigger=1))
        if variant in ('heal-rearms-value','scaled-maximum'):extra[N[0]].append(E('restore health','instant','heal_hp_pct',100,event='every:0.4s',max_trigger=1))
        if variant in ('source-down-buff-remains','source-revives','scaled-maximum-revival'):
            b['enemy']['patterns']=[s.lethal(at=.2)]
            if variant!='source-down-buff-remains':extra[N[2]].append(E('revive source','instant','revive',50,'allies_down_top_atk_excl:1',event='event:ally_down',max_trigger=1))
        yield name,b,extra
    variants=('no-broken-cover','only-broken-revives','recipient-maximum','healing-cannot-revive','ordinary-heal-living-positive','repeat-revival','random-includes-caster','random-excludes-down','cover-condition-rearms','overmaximum-percentage','stack-reference','empty-budget-then-break','ordered-list-duplicates','revive-then-heal','registered-timer-source-down')
    for variant in variants:
        b=body(2,scalar=0);extra={n:[] for n in N};random_case=variant.startswith('random-') or variant in ('empty-budget-then-break','ordered-list-duplicates','registered-timer-source-down')
        if variant!='no-broken-cover':b['enemy']['patterns']=[dict(id='break covers',kind='attack',delay=.25 if variant=='empty-budget-then-break' else .1,until={'time':.7},spec=dict(coeff=100,atk=1000000 if variant=='ordinary-heal-living-positive' else 5000000,target='all' if random_case else 'slot:1',hits=2 if variant=='repeat-revival' else 1,interval=.4))]
        if variant in ('random-excludes-down','registered-timer-source-down'):b['enemy']['patterns'].append(s.lethal('slot:5' if variant=='random-excludes-down' else 'slot:1',at=.15))
        extra[N[0]]+=[E('take cover','instant','force_reload',0,'all_allies'),B('cover healed witness','atk_pct',11,event='event:cover_healed',max_stack=100)]
        if variant=='recipient-maximum':extra[N[0]].append(B('recipient cover maximum','cover_hp_pct',50))
        if variant in ('healing-cannot-revive','ordinary-heal-living-positive'):extra[N[0]].append(E('ordinary healing','instant','cover_heal_pct',100,event='every:0.3s',max_trigger=1))
        else:
            target='allies_broken_cover_random:2' if random_case else 'all_allies'
            if variant=='ordered-list-duplicates':target=['self',target,'self']
            kw=dict(event='every:0.1s' if variant=='empty-budget-then-break' else 'every:0.3s',max_trigger=2 if variant=='repeat-revival' else 1)
            if variant=='registered-timer-source-down':kw=dict(tick_interval=.3,duration=1)
            if variant=='stack-reference':
                extra[N[0]].append(B('restore factor','',event='every:0.05s',max_stack=2));kw.update(scaling='stack_count',scaling_ref='restore factor')
            extra[N[0]].append(E('revive cover','instant','cover_revive',75 if variant=='recipient-maximum' else 150 if variant=='overmaximum-percentage' else 50,target,**kw))
        if variant=='cover-condition-rearms':
            e=B('broken-cover power','atk_pct',50,event='passive');e['trigger']['condition']=['not_self_cover_alive'];extra[N[0]].append(e)
        if variant=='revive-then-heal':extra[N[0]].append(E('heal restored cover','instant','cover_heal_pct',25,'all_allies',event='every:0.4s',max_trigger=1))
        yield 'cover-'+variant,b,extra

def real_fixtures():
    for character in ('목단','비스킷'):
        for variant in ('no-shots','incoming','accumulate','revival'):
            names=[character,N[1],N[3],N[2],N[0]] if character=='목단' else [N[0],character,N[3],N[2],N[4]]
            if variant=='revival':names=['라푼젤',N[0],N[1],character,N[3]]
            b=body(30,True,names);b['burst_gauge_mode']='accumulate' if variant=='accumulate' else 'fixed';extra={n:[] for n in names}
            if variant in ('incoming','accumulate'):
                extra[names[0]].append(B('test survival support','undying',1,'all_allies'))
                if character=='비스킷':extra[names[0]].append(E('initial cover','instant','force_reload',0,'all_allies'))
                b['enemy']['patterns']=[dict(id='damage',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=5000000 if character=='비스킷' else 800000,target='all' if character=='비스킷' else 'slot:1',hits=6 if character=='비스킷' else 60,interval=4 if character=='비스킷' else .5,pierce=character=='목단'))]
            if variant=='revival':b['enemy']['patterns']=[s.lethal('slot:4',2.8)]
            yield 'raw-'+character+'-'+variant,b,extra

def compare(device,name,b,extra,backend):
    frames=[];down_frames=[];scalars=[];captured={};revived=[];cover_healed=[];hp_events=[];code=s.timeline.simulate.__code__
    lines,first=inspect.getsourcelines(s.timeline.simulate);tree=ast.parse(textwrap.dedent(''.join(lines)))
    advance=[n for n in ast.walk(tree) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='t' and isinstance(n.value,ast.Name) and n.value.id=='DT'];assert len(advance)==1
    end_line=first+advance[0].lineno-1;names=b['squad']
    def state_snapshot(state):return {n:dict(hp=state['hp'][n],cover_hp=state['cover_hp'][n],cover_max_hp=state['cover_max_hp'][n]) for n in names}
    def down_mask(state):return sum(1<<i for i,n in enumerate(names) if n in state.get('down',set()))
    def trace(frame,event,arg):
        if frame.f_code is not code:return None
        local=frame.f_locals
        if event=='line' and frame.f_lineno==end_line:
            frames.append(dict(time=local['t'],state=state_snapshot(local['state'])));down_frames.append(dict(time=local['t'],mask=down_mask(local['state'])))
            if b.get('_debug_scalar_query') is not None:
                who=b['_debug_scalar_query']['who'];value=local['bm'].get_buffs(names[who],'reference-enemy',local['t']).get('atk_pct',0);scalars.append(dict(time=local['t'],value=value))
        if event=='return':
            state=local['state'];captured.update(state=state_snapshot(state),hp_pct={n:state['hp_pct'][n] for n in names},down=down_mask(state),boss_rng=list(local['boss_rng'].getstate()[1]),control={n:dict(charging=bool(state.get('charging',{}).get(n,False)),ammo=local['char_states'][n].ammo,reloading_until=local['char_states'][n].reloading_until) for n in names})
        return trace
    original_notify=BuffManager.notify;original_revive=s.CharState.on_revive
    def notify(self,event,t,caster,**kwargs):
        if event=='event:cover_healed':cover_healed.append(dict(time=t,caster=caster))
        if event in self._notify_index.get(caster,{}) and event.startswith(('hp_below:','event:ally_hp_below:','event:adjacent_hp_')):hp_events.append(dict(time=t,caster=caster,event=event))
        return original_notify(self,event,t,caster,**kwargs)
    def on_revive(self,t,bm):revived.append(dict(name=self.name,time=t));return original_revive(self,t,bm)
    with s.v.context(name,extra):
        compiled=s.v.v.a.evaluate({**b,'_compile_gpu_detail':True});gpu=g.evaluate_full(device,compiled,module_backend=backend)
        previous=sys.gettrace()
        with patch.object(BuffManager,'notify',notify),patch.object(s.CharState,'on_revive',on_revive):
            try:sys.settrace(trace);cpu=s.v.v.a.evaluate(b)
            finally:sys.settrace(previous)
        skill_rng=list(random.getstate()[1])
    checks=s.v.v.v.resolve_verification(gpu,cpu)['compute']['cpu_verification']
    control={n:{k:gpu['compute']['final_control'][n][k] for k in ('charging','ammo','reloading_until')} for n in names}
    checks.update(actual_gpu=gpu['compute']['backend']=='cuda_detail',incoming_frames=s.v.close(gpu['_incoming_frames'],frames),final_state=s.v.close(gpu['_incoming_state'],captured['state']),down_frames=gpu['_down_frames']==down_frames,final_down=gpu['_down_mask']==captured['down'],boss_rng=gpu['_boss_random_state']==captured['boss_rng'],skill_rng=gpu['_random_state']==skill_rng,final_control=s.v.close(control,captured['control']),hp_event_order=s.v.close(gpu['_hp_events'],hp_events))
    if scalars:checks['scalar_frames']=s.v.close(gpu.get('_scalar_frames'),scalars)
    checks['final_HP_percentages']=s.v.close({n:gpu['compute']['final_hp'][n]['hp_pct'] for n in names},captured['hp_pct'])
    if name in ('lost-source-revives','lost-scaled-maximum-revival') or name.startswith('raw-') and name.endswith('-revival'):checks['revival_exercised']=bool(revived)
    if name.startswith('cover-'):
        expected=1 if name=='cover-ordinary-heal-living-positive' else 5 if name=='cover-revive-then-heal' else 0
        checks['cover_healed_notification_control']=len(cover_healed)==expected
        if name not in ('cover-no-broken-cover','cover-ordinary-heal-living-positive'):checks['broken_cover_exercised']=any(any(c['cover_hp']==0 for c in f['state'].values()) for f in frames)
        def transitions(sequence):return [dict(time=now['time'],character=n,hp=now['state'][n]['cover_hp']) for before,now in zip(sequence,sequence[1:]) for n in names if before['state'][n]['cover_hp']==0 and now['state'][n]['cover_hp']>0]
        cpu_cover_transitions=transitions(frames);gpu_cover_transitions=transitions(gpu['_incoming_frames'])
        checks['cover_revival_transitions']=s.v.close(gpu_cover_transitions,cpu_cover_transitions)
        checks['cover_revival_positive_control']=bool(cpu_cover_transitions)==(name not in ('cover-no-broken-cover','cover-healing-cannot-revive','cover-ordinary-heal-living-positive'))
        if name=='cover-repeat-revival':checks['repeated_cover_revival_exercised']=len(cpu_cover_transitions)==2
    r=dict(name=name,backend=backend,passed=all(checks.values()),checks=checks,cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],cpu_cover_healed=cover_healed,cpu_hp_events=hp_events,cpu_revives=revived,raw_skills_retained=name.startswith('raw-'))
    if not checks['incoming_frames']:r['frame_difference']=next((dict(index=i,cpu=c,gpu=x) for i,(c,x) in enumerate(zip(frames,gpu['_incoming_frames'])) if not s.v.close(c,x)),None)
    if scalars and not checks['scalar_frames']:r['scalar_difference']=next((dict(index=i,cpu=c,gpu=x) for i,(c,x) in enumerate(zip(scalars,gpu.get('_scalar_frames',[]))) if not s.v.close(c,x)),dict(cpu_count=len(scalars),gpu_count=len(gpu.get('_scalar_frames',[]))))
    if not checks['skill_rng']:r['skill_rng_difference']=next((dict(index=i,cpu=c,gpu=x) for i,(c,x) in enumerate(zip(skill_rng,gpu['_random_state'])) if c!=x),None)
    print(json.dumps(r,ensure_ascii=True),flush=True);return r

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],default='native');ap.add_argument('--real',action='store_true');ap.add_argument('--fail-fast',action='store_true');ap.add_argument('--output',required=True);args=ap.parse_args()
    files=['scripts/verify-staged-survival-scaling.py','scripts/staged-survival-scaling-runtime.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/survival_compat.py','app/engine_compat.py','app/engine_worker.py','app/detail_world.py','app/detail_boss.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json']+['research/staging/v36/app/'+n for n in (('detail_gpu.py','survival_scaling_compat.py','detail_effects.cu','detail_effects.ptx','detail_effects-build.json') if args.backend=='ptx' else ('detail_gpu.py','survival_scaling_compat.py','detail_effects.cu','detail_effects-sm86.cubin','detail_effects-sm86.json'))]
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};planned=list(real_fixtures() if args.real else fixtures());rows=[];device=s.v.v.v.Cuda()
    try:
        for name,b,extra in planned:
            try:r=compare(device,name,b,extra,args.backend)
            except Exception as exc:r=dict(name=name,passed=False,error=repr(exc));print(json.dumps(r),flush=True)
            rows.append(r)
            if args.fail_fast and not r['passed']:break
    finally:device.close()
    assert hashes=={p:sha(p) for p in files}
    r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(x['passed'] for x in rows),stage_only=True,objective_complete=False,abi=g.DETAIL_ABI,backend=args.backend,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
    (ROOT/args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
