"""Passive observations of canonical manual primitives and their final state."""
import sys
from contextlib import contextmanager

@contextmanager

def capture(case):
    import engine_worker
    from calculator import timeline
    from world_frame_native import roster_names
    names=roster_names(case);previous=sys.getprofile();events=[];characters={};managers=[];squad_pumps=[]
    methods=('_enter_cover','_exit_cover','_cancel_reload','_finish_reload','_reset_action')+(('_auto_reload',) if case.get('observe_auto_reload') else ())
    codes={getattr(timeline.CharState,k).__code__:k for k in methods}
    arb=timeline._arbitrate_control.__code__;charge=timeline.CharState._tick_charge.__code__
    burst_tick=timeline.BurstController.tick.__code__;burst_ticks=[]
    squad_tick=timeline._pump_squad_seq.__code__
    observed_codes=set(codes)|{arb,charge}
    if case.get('burst_controls'):observed_codes.add(burst_tick)
    if case.get('squad_controls'):observed_codes.add(squad_tick)
    def state(cs,bm=None):
        if bm is None:bm=managers[0]
        extra=dict(cover_all=bool(cs._cover_all)) if case.get('squad_controls') else {}
        if case.get('observe_auto_reload'):extra['pending_auto_reload']=bool(cs._pending_auto_reload)
        return dict(**extra,phase=cs._charge_phase,charging_visible=bool(bm.state.get('charging',{}).get(cs.name,False)),owner=names.index(cs.name),until=cs._cover_until,until_reload=cs._cover_until_reload,cancel_after_clip=cs._reload_cancel_after_clip,ammo=cs.ammo,reload_until=cs.reloading_until,sequence_index=cs._ctrl_seq_i)
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if event!='return':return
        if frame.f_code not in observed_codes:return
        v=frame.f_locals
        if case.get('burst_controls') and frame.f_code==burst_tick:
            from world_burst_control_native import snapshot
            burst_ticks.append(snapshot(v['self'],v['t'],names))
        if frame.f_code==arb:characters.update(v['char_states']);managers[:]=[v['bm']]
        if case.get('squad_controls') and frame.f_code==squad_tick:
            q=v['bm'].state;forced=q.get('ctrl_focus_forced') or '';keep=v.get('keep') or ''
            squad_pumps.append(dict(time=v['t'],index=q['_squad_seq_i'],owner=names.index(q['ctrl_owner']) if q['ctrl_owner'] else -1,forced=names.index(forced)+1 if forced else 0,keep=(names.index(keep)+1 if keep else 0) if 'keep' in v else None))
            if case.get('squad_mode_state'):squad_pumps[-1]['mode_mask']=sum(1<<who for who,name in enumerate(names) if v['char_states'][name]._in_weapon_change)
        if frame.f_code==charge and '_entry' in v:
            cs=v['self'];events.append(dict(kind='_charge_start',time=v['t'],**state(cs,v.get('bm'))))
        if frame.f_code in codes:
            cs=v['self'];characters[cs.name]=cs
            events.append(dict(kind=codes[frame.f_code],time=v['t'],**state(cs,v.get('bm'))))
    sys.setprofile(profile)
    observed={}
    try:yield observed
    finally:sys.setprofile(previous)
    if set(characters)!=set(names):raise ValueError('Missing canonical manual character state')
    observed['manual_actions']=dict(events=events,characters=[state(characters[name]) for name in names])
    if case.get('squad_controls'):
        last=squad_pumps[-1];keeps=[p['keep'] for p in squad_pumps if p['keep'] is not None]
        observed['squad_control']=dict(sequence_index=last['index'],forced_owner=last['forced'],last_keep=keeps[-1] if keeps else 0,pumps=squad_pumps)
    if case.get('squad_mode_state'):observed['squad_mode_state']=dict(flags=[bool(characters[name]._in_weapon_change) for name in names],pumps=[dict(time=p['time'],mask=p['mode_mask']) for p in squad_pumps])
    if case.get('cover_policies'):observed['cover_policy_state']=[dict(cover_anchor=characters[name]._cover_ctrl_anchor,reload_anchor=characters[name]._reload_ctrl_anchor,kind=characters[name]._ctrl_anchor_kind,value=characters[name]._ctrl_anchor_val,reentry=sorted([list(v) for v in characters[name]._reentry_used if v[0] in ('cover','reload')])) for name in names]
    if case.get('burst_controls'):
        if not burst_ticks:raise ValueError('Missing canonical burst ticks')
        observed['burst_controls']=dict(ticks=burst_ticks)

def observe(case):
    from world_coordinate_sampled_delivery_native import observe as parent
    with capture(case) as observed:n,t=parent(case)
    n.update(observed);return n,t
