"""Independent pinned BurstController/BuffManager, evaluated after GPU readback.
Only static authored weapon metadata is supplied; no CPU states become GPU input.
"""
import copy
import math
import engine_worker
from calculator import timeline,buff_manager
from calculator.buff_manager import BuffManager
from portable_weapon_oracle import authored_weapon,authored_weapon_state
from timer_registry_cases import NAMES


def _observe(case):
    config=case['combat'];weapons=config['weapons'];attacks=case.get('base_atk',[1000]*5)
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES]
    for c,w in zip(chars,weapons):authored_weapon(c,w)
    raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))]
    class BM(BuffManager):
        def _register_all(self):self._effects=raw;self._build_notify_index()
        def char_effects(self,name):return [e for e,n in raw if n==name]
    state=dict(base_stats={n:dict(atk=a,hp=1000000,**{'def':0}) for n,a in zip(NAMES,attacks)},
               full_burst=False,rng_acc={},rng_expected=True,burst_casted={},burst_cycle_users={},
               burst_stages={n:str(w.get('stage',0)) for n,w in zip(NAMES,weapons)},
               burst_gauge=config.get('initial_gauge',0),burst_gauge_charging=True,camera=set())
    enemy=dict(defense=0,core_px=0,code=case.get('environment',{}).get('enemy_code'),optimal_range_weapons=[],**{'def':config['targets'][0].get('defense',0)})
    state['enemy']=enemy;bm=BM(chars,state=state)
    actors={n:authored_weapon_state(c,w,a) for n,c,w,a in zip(NAMES,chars,weapons,attacks)}
    counts=[0]*5;casts=[];shots=[0]*5;damage=[0]*5
    for name,w in zip(NAMES,weapons):actors[name].reload_cancel_on_full=w.get('reload_cancel_on_full',False)
    class Controller(timeline.BurstController):
        def _cast_burst(self,name,stage,t,bm,state):
            counts[NAMES.index(name)]+=1;casts.append(dict(time=t,owner=NAMES.index(name),stage=int(stage)))
            return super()._cast_burst(name,stage,t,bm,state)
    ctrl=Controller(chars,dict(burst_gauge_mode='accumulate'),actors,enemy)
    timeline._register_instant_handlers(bm,actors,ctrl)
    commands=[];next_frame=0;clock=0.0;accumulated=config.get('clock')=='accumulated'
    for command in case['script']:
        if command[1]==24:
            while next_frame<=10800 and (clock if accumulated else next_frame/60)<=command[0]:
                commands.append([clock if accumulated else next_frame/60,4,0,0,0,-1,0,0]);next_frame+=1
                if accumulated:clock+=1/60
        else:commands.append(command)
    started=False;queries=[]
    for t,op,event,who,arg,index,extra,extra2 in commands:
        if op==4:
            if not started:
                for n in NAMES:bm.notify('battle_start',t,n)
                for n,a in actors.items():a.ammo=a._full_ammo(bm,t)
                started=True
            bm.tick(t);ctrl.tick(t,bm,state)
            for n,w in zip(NAMES,weapons):
                if w.get('enabled',False):
                    hits=actors[n].tick(t,bm,enemy,{'rng_mode':'expected'});i=NAMES.index(n);shots[i]+=int(bool(hits));damage[i]+=sum(h.damage for h in hits)
        elif op==0:
            bm.notify({17:'event:cover_healed',3:'burst_cast',7:'on_attack',8:'hit_count',14:'last_bullet',19:'event:full_reload'}[event],t,NAMES[who])
        elif op==2:
            phase=ctrl._phase
            phase=0 if phase=='idle' else 4 if phase=='switching' else 5 if phase=='full_burst' else int(phase.split(':')[1])
            queries.append(dict(combat=dict(full_end=max(0,ctrl._full_burst_end_t),last_b3_caster=NAMES.index(ctrl._fb_caster) if ctrl._fb_caster else -1,last_b3_cast_time=ctrl._fb_caster_t,last_full_start=ctrl._last_fb_start_t,phase=phase,gauge=state['burst_gauge'],gauge_charging=state['burst_gauge_charging'],
                    cast_mask=sum(1<<i for i,n in enumerate(NAMES) if state['burst_casted'].get(n)),casts=counts.copy(),
                    cooldown_wait_mask=sum(1<<NAMES.index(n) for n in (ctrl._cd_wait_candidates or [])),
                    cooldown_applied=[ctrl._cd_applied_at_cast[n] for n in NAMES],
                    weapons=[dict(ready=ctrl.burst_ready_at[n]) for n in NAMES])))
            if (case.get('ammo_reference') or case.get('mode_session_reference')):
                queries[-1]['damage']=damage.copy()
                queries[-1]['combat']['weapons']=[dict(ready=ctrl.burst_ready_at[n],ammo=actors[n].ammo,shots=shots[i],reload_until=actors[n].reloading_until,next=actors[n].next_fire_time) for i,n in enumerate(NAMES)]
            if (case.get('ammo_reference') or case.get('mode_session_reference')):
                for name,projection in zip(NAMES,queries[-1]['combat']['weapons']):
                    actor=actors[name];mode=bm.get_weapon_change(name)
                    if case.get('mode_session_reference'):projection['mode_shots']=actor._wc_shots if mode is not None else 0
                    projection['mode_index']=next((i for i,(e,n) in enumerate(raw) if n==name and e.get('type')=='weapon_change' and mode is not None and e.get('name')==mode.get('name')),-1)
                    charge=bool(mode.get('charge')) if mode is not None else actor.fire_mode=='charge'
                    if charge:
                        projection.pop('next')
                        if actor._charge_phase=='charging':projection.update(charging=True,charge_until=actor._charge_end_t)
                        else:projection.update(charging=False,next=actor._post_delay_end_t)
            queries[-1]['attack_buffs']=[bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES]
            if 1<=phase<=4:queries[-1]['combat']['action']=ctrl._next_action_t if math.isfinite(ctrl._next_action_t) else 1e30
        else:raise ValueError('Burst oracle supports frames, notifications and queries')
    result=dict(queries=queries,casts=casts)
    if case.get('mode_timing_reference'):
        result['weapon_timings']={i:dict(warm=actors[n].warmup_shots,last_fire=actors[n].last_fire_t,last_interval=actors[n]._last_inter)
                                  for i,(n,w) in enumerate(zip(NAMES,weapons)) if w.get('enabled',False)}
    return result


def observe(case):
    tables=[]
    for table in (buff_manager._NIKKE,timeline._NIKKE):
        if not any(table is prior for prior,_ in tables):tables.append((table,{n:table[n] for n in NAMES}))
    try:
        for table,saved in tables:
            for n,w in zip(NAMES,case['combat']['weapons']):
                metadata=dict(saved[n]);metadata.update(burst_stage=str(w.get('stage',0)),burst_cooldown=w.get('cooldown',40))
                metadata['charge_time']=w.get('charge',1) if w.get('mode')=='charge' else 0
                table[n]=metadata
        return _observe(case)
    finally:
        for table,saved in tables:
            for n,metadata in saved.items():table[n]=metadata
