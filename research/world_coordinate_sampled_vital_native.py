"""Observe actual live weapons and health handler returns without scheduling."""
import sys

def observe(case,*,shot_codes=None):
    import engine_worker
    from calculator import timeline
    from world_frame_native import roster_names
    from world_coordinate_sampled_burst_native import observe as parent
    names=roster_names(case);previous=sys.getprofile();shots=[];health=[]
    codes={timeline.CharState._fire.__code__,timeline.CharState._charge_fire.__code__} if shot_codes is None else set(shot_codes)
    handlers={'handle_heal_hp_pct','handle_current_hp_reduce','handle_cover_heal_pct','_apply_lifesteal'}
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        v=frame.f_locals
        if frame.f_code in codes and event=='return' and answer:
            cs=v['self'];shots.append(dict(owner=names.index(cs.name),time=v['t'],mode=bool(cs._in_weapon_change),kind=frame.f_code.co_name,weapon_type=cs.weapon_type,pellets=cs.pellets,muzzles=cs.muzzles,coefficient=cs.weapon['damage_coeff']))
            if case.get('sampled_delivery'):shots[-1]['skill_damage']=cs._wc_is_skill_damage()
        if event=='return' and frame.f_code.co_name in handlers:
            bm=v.get('bm')
            if bm is None:raise ValueError('Canonical health manager missing')
            eff=v.get('eff');ev=v.get('ev');health.append(dict(kind=frame.f_code.co_name,time=v['t'],name=eff['name'] if eff else ev.skill_name,hp=[bm.state['hp'][n] for n in names],cover=[bm.state['cover_hp'][n] for n in names]))
    sys.setprofile(profile)
    try:n,t=parent(case)
    finally:sys.setprofile(previous)
    n.update(sampled_live_shots=shots,sampled_health_returns=health)
    return n,t
