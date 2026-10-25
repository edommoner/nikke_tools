"""Passive observations of canonical manual primitives and their final state."""
import sys

def observe(case):
    import engine_worker
    from calculator import timeline
    from world_frame_native import roster_names
    from world_coordinate_sampled_delivery_native import observe as parent
    names=roster_names(case);previous=sys.getprofile();events=[];characters={};managers=[]
    methods=('_enter_cover','_exit_cover','_cancel_reload','_finish_reload','_reset_action')
    codes={getattr(timeline.CharState,k).__code__:k for k in methods}
    arb=timeline._arbitrate_control.__code__;charge=timeline.CharState._tick_charge.__code__
    def state(cs,bm=None):
        if bm is None:bm=managers[0]
        return dict(phase=cs._charge_phase,charging_visible=bool(bm.state.get('charging',{}).get(cs.name,False)),owner=names.index(cs.name),until=cs._cover_until,until_reload=cs._cover_until_reload,cancel_after_clip=cs._reload_cancel_after_clip,ammo=cs.ammo,reload_until=cs.reloading_until,sequence_index=cs._ctrl_seq_i)
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if event!='return':return
        v=frame.f_locals
        if frame.f_code==arb:characters.update(v['char_states']);managers[:]=[v['bm']]
        if frame.f_code==charge and '_entry' in v:
            cs=v['self'];events.append(dict(kind='_charge_start',time=v['t'],**state(cs,v.get('bm'))))
        if frame.f_code in codes:
            cs=v['self'];characters[cs.name]=cs
            events.append(dict(kind=codes[frame.f_code],time=v['t'],**state(cs,v.get('bm'))))
    sys.setprofile(profile)
    try:n,t=parent(case)
    finally:sys.setprofile(previous)
    if set(characters)!=set(names):raise ValueError('Missing canonical manual character state')
    n['manual_actions']=dict(events=events,characters=[state(characters[name]) for name in names])
    if case.get('cover_policies'):n['cover_policy_state']=[dict(cover_anchor=characters[name]._cover_ctrl_anchor,reload_anchor=characters[name]._reload_ctrl_anchor,kind=characters[name]._ctrl_anchor_kind,value=characters[name]._ctrl_anchor_val,reentry=sorted([list(v) for v in characters[name]._reentry_used if v[0] in ('cover','reload')])) for name in names]
    return n,t
