"""Complete real preparation -> shared GPU frames -> original CPU simulation.
The fixed profiles below are evidence for those squads, not all-character or
variant certification. CPU observers are installed only after GPU readback.
"""
import argparse,copy,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker as adapter
from calculator import timeline
from detail_coverage import body_for
from portable_roster_input import compile_static_battle
from portable_runtime import run_programs,UnsupportedPortable


def native_reference(body):
    observed={};counts={};capture={};physical_modes={};original_char=timeline.CharState;original_burst=timeline.BurstController;original_execute=adapter.sim.execute
    class Character(original_char):
        def _tick_auto(self,*args,**kwargs):
            physical_modes[self.name]=self.fire_mode
            return super()._tick_auto(*args,**kwargs)
        def _tick_charge(self,*args,**kwargs):
            physical_modes[self.name]=self.fire_mode
            return super()._tick_charge(*args,**kwargs)
        def tick(self,*args,**kwargs):
            hits=super().tick(*args,**kwargs);observed[self.name]=self;counts[self.name]=counts.get(self.name,0)+int(bool(hits));return hits
    class Controller(original_burst):
        def tick(self,t,bm,state):
            events=super().tick(t,bm,state);capture.update(controller=self,bm=bm,state=state,time=t);return events
    def execute(run):
        result=original_execute(run);capture['result']=result;return result
    try:
        timeline.CharState=Character;timeline.BurstController=Controller;adapter.sim.execute=execute
        payload=adapter.evaluate(copy.deepcopy(body))
        ctrl,bm,state=capture['controller'],capture['bm'],capture['state'];names=body['squad']
        phase=ctrl._phase;phase_id=0 if phase=='idle' else 4 if phase=='switching' else 5 if phase=='full_burst' else int(phase.split(':')[1])
        trace=[]
        for event in capture['result'].log.burst_log:
            match=re.fullmatch(r'(stage|reenter):([123]) 사용',event.event)
            code=int(match[2])+(6 if match[1]=='reenter' else 0) if match else 4 if event.event=='full_burst 시작' else 5 if event.event=='full_burst 종료' else 6 if event.event.startswith('게이지 만충') else None
            if code is not None:trace.append(dict(time=event.t,event=code,owner=names.index(event.caster) if event.caster else -1))
        final=dict(covers=[dict(hp=bm.state['cover_hp'][n],max_hp=bm.state['cover_max_hp'][n],effective_max_hp=bm.cover_max_hp(n,capture['time'])) for n in names],body_damage=[next(x['damage'] for x in payload['members'] if x['name']==n) for n in names],
            combat=dict(last_b3_caster=names.index(ctrl._fb_caster) if ctrl._fb_caster else -1,last_b3_cast_time=ctrl._fb_caster_t,last_full_start=ctrl._last_fb_start_t,phase=phase_id,cast_mask=sum(1<<i for i,n in enumerate(names) if state['burst_casted'].get(n)),gauge=state['burst_gauge'],
                full_end=max(0,ctrl._full_burst_end_t),gauge_charging=state['burst_gauge_charging'],cooldown_applied=[ctrl._cd_applied_at_cast[n] for n in names],
                weapons=[dict(ammo=observed[n].ammo,shots=counts[n],charge_until=observed[n]._charge_end_t,reload_until=observed[n].reloading_until,
                              ready=ctrl.burst_ready_at[n],charging=observed[n]._charge_phase=='charging') for n in names]),
            allies=[dict(hp=state['hp'][n],max_hp=bm.effective_max_hp(n),hp_pct=state['hp_pct'][n],defense=bm._effective_def(n)) for n in names])
        gates=[];active_modes=[]
        for owner,n in enumerate(names):
            actor=observed[n]
            mode=bm.get_weapon_change(n)
            fire_mode=physical_modes.get(n,actor.fire_mode) if mode is not None else actor.fire_mode
            if mode is not None:
                definitions=[i for i,(effect,caster) in enumerate(bm._effects) if effect is mode and caster==n]
                assert len(definitions)==1,'Native active-mode identity is not unique'
                active_modes.append(dict(owner=owner,definition=definitions[0],name=mode.get('name'),shots=actor._wc_shots,fire_mode=fire_mode,physical_active=actor._in_weapon_change))
            if actor.reloading_until>=0:gate=dict(kind='reload',time=actor.reloading_until)
            elif actor._post_reload_end_t>=0:gate=dict(kind='post_reload',time=actor._post_reload_end_t)
            elif fire_mode=='charge':
                gate=dict(kind='charge',time=actor._charge_end_t) if actor._charge_phase=='charging' else dict(kind='charge_delay',time=actor._post_delay_end_t)
            else:gate=dict(kind='fire',time=actor.next_fire_time)
            gates.append(gate)
        result=dict(query=final,action_gates=gates,inactive_cpu_timestamps=[dict(next_fire_time=observed[n].next_fire_time,post_delay_end=observed[n]._post_delay_end_t) for n in names],weapon_states=[dict(charge_started_at=observed[n]._charge_start_t,post_reload_until=observed[n]._post_reload_end_t,pending_auto_reload=observed[n]._pending_auto_reload) for n in names],state_projection='Compare the active reload/post-reload/charge/fire gate; inactive implementation timestamps are diagnostic only',burst_trace=trace,base_stats=payload['base_stats'],total_damage=payload['total_damage'],last_frame=capture['time'],cpu_engine_revision=payload['engine_revision'])
        if active_modes:result['active_weapon_modes']=active_modes
        return result
    finally:
        timeline.CharState=original_char;timeline.BurstController=original_burst;adapter.sim.execute=original_execute


def differences(actual,expected,path=''):
    rows=[]
    if isinstance(expected,dict):
        for key,value in expected.items():rows+=differences(actual[key],value,path+'.'+key)
    elif isinstance(expected,list):
        if len(actual)!=len(expected):return [dict(path=path,actual_length=len(actual),expected_length=len(expected))]
        for i,value in enumerate(expected):rows+=differences(actual[i],value,path+f'[{i}]')
    elif actual!=expected:rows.append(dict(path=path,gpu=actual,cpu=expected))
    return rows


def action_gate(weapon,extra,fire_mode):
    if weapon['reload_until']>=0:return dict(kind='reload',time=weapon['reload_until'])
    if extra['post_reload_until']>=0:return dict(kind='post_reload',time=extra['post_reload_until'])
    if weapon['charging']:return dict(kind='charge',time=weapon['charge_until'])
    return dict(kind='charge_delay' if fire_mode=='charge' else 'fire',time=weapon['next'])

def compare_native_result(gpu,p,cpu,*,program=None):
    query=gpu['queries'][0]
    gates=[];mode_diffs=[];active={row['owner']:row for row in cpu.get('active_weapon_modes',[])}
    for owner,(w,extra,descriptor) in enumerate(zip(query['combat']['weapons'],gpu['weapons'],p['weapons'])):
        fire_mode=descriptor['mode'];expected=active.get(owner)
        mode_diffs+=differences(w,dict(mode_index=expected['definition'] if expected else -1),f'weapon_modes[{owner}]')
        if w['mode_index']>=0:
            from portable_specs import LIMITS as L
            if program is None:program=compile_static_battle(p,trace='burst')
            definition=w['mode_index'];assert 0<=definition<len(p['effects']) and p['effects'][definition]['effect']['type']=='weapon_change','Invalid active GPU mode definition'
            fire_mode={0:'auto',1:'charge',2:'auto_warmup'}[program[0][L['MODE_BASE']+definition*L['MODE_WORDS']]]
            if expected:
                mode_diffs+=differences(dict(shots=w['mode_shots'],fire_mode=fire_mode),dict(shots=expected['shots'],fire_mode=expected['fire_mode']),f'weapon_modes[{owner}]')
        gates.append(action_gate(w,extra,fire_mode))
    diff=differences(query,cpu['query'])+differences(gpu['burst_trace'],cpu['burst_trace'],'burst_trace')+differences(gpu['weapons'],cpu['weapon_states'],'weapon_states')+differences(gates,cpu['action_gates'],'action_gates')
    for i,c in enumerate(p['chars']):
        expected=dict(atk=p['base_atk'][i],hp=p['allies'][i]['base_hp'],**{'def':p['allies'][i]['base_defense']})
        assert cpu['base_stats'][c['name']]==expected
    return diff+mode_diffs


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('metal','cuda'),default='metal');args=parser.parse_args()
    path=ROOT/f'research/portable-real-battle-{args.backend}.json';path.write_text(json.dumps(dict(passed=False,stage='preparing'))+'\n')
    tracked=[p for folder in ('app','scripts') for p in (ROOT/folder).glob('*.py')]
    tracked += [p for folder in ('calculator','runner','data') for p in (ROOT/'research/upstream/nikke-calc-master'/folder).rglob('*') if p.suffix in ('.py','.json')]
    tracked += [ROOT/'data/engine-effect-overrides.json',ROOT/'scripts/run-metal-probe.swift']
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(tracked))}
    bodies=[{**body_for(['미란다','도라','드레이크','N102','메어리'],duration=t,grown=g),'burst_gauge_mode':'accumulate'} for t,g in [(3,False),(30,False),(180,False),(180,True)]]
    bodies += [{**body_for(['미란다','도라','브리드','N102','메어리'],duration=t,grown=g),'burst_gauge_mode':'accumulate'} for t,g in [(3,False),(30,False),(180,False),(180,True)]]
    prepared=[adapter.evaluate({**body,'_portable_static_inputs':True}) for body in bodies]
    programs=[];indices=[];gaps={}
    for index,p in enumerate(prepared):
        try:program=compile_static_battle(p,trace='full')
        except UnsupportedPortable as error:gaps[index]=str(error)
        else:programs.append(program);indices.append(index)
    result=run_programs(programs,backend=args.backend);result.update(passed=False,stage='readback-before-original-CPU',validation_sha256=hashes,
        real_prepared_input_connected=True,normal_ui_connected=False,full_character_verified=0,all_character_effects_included=True,cpu_trace_used_as_gpu_input=False,
        scope='Eight fixed real all-effect squad/profile cases; static simple boss, no manual controls, expected accumulate mode; not all variants or catalog')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    cases=[]
    for index,gpu in zip(indices,result['results']):
        body,p=bodies[index],prepared[index]
        cpu=native_reference(body);query=gpu['queries'][0]
        diff=compare_native_result(gpu,p,cpu)
        cases.append(dict(squad=body['squad'],duration=body['duration'],grown=body['profile']['chars'][body['squad'][0]]['collection_stage']=='SR15',passed=not diff,
                          prepared_effects=len(p['effects']),cpu_battle_executed_for_gpu_input=p['cpu_battle_executed'],native_reference=cpu,differences=diff))
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
    for index,error in gaps.items():
        body=bodies[index];cases.append(dict(squad=body['squad'],duration=body['duration'],grown=body['profile']['chars'][body['squad'][0]]['collection_stage']=='SR15',passed=False,compile_error=error,prepared_effects=len(prepared[index]['effects']),differences=[]))
    passed=not gaps and all(c['passed'] for c in cases)
    result.update(cases=cases,passed=passed,stage='verified' if passed else 'real-input-gaps' if gaps else 'native-CPU-differences')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],cases=[{k:c[k] for k in ('duration','grown','passed','differences','compile_error') if k in c} for c in cases]),ensure_ascii=False))
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
