"""Observe native body lifesteal locals without adding numeric queries or hits."""
import sys
from world_destructible_weapon_roster_native import observe as prior


def observe(case):
    previous=sys.getprofile();events=[];pending={};names=case['body']['squad']
    def profile(frame,event,value):
        if previous is not None:previous(frame,event,value)
        if frame.f_code.co_name!='_apply_lifesteal' or event not in ('call','return'):return
        local=frame.f_locals
        if 'ev' not in local or 'bm' not in local or 'base_stats' not in local:return
        ev=local['ev'];manager=local['bm']
        if event=='call':
            row=dict(owner=names.index(ev.caster),time=local['t'],damage=ev.damage,before=manager.state['hp'][ev.caster],tag=ev.hit_tag,name=ev.skill_name,caller=frame.f_back.f_code.co_name)
            events.append(row);pending[id(frame)]=row
        else:
            row=pending.pop(id(frame))
            if 'ls' not in local:
                row['failed']=True
                return
            row.update(after=manager.state['hp'][ev.caster],rate=local['ls'],heal=local.get('heal',0.))
    sys.setprofile(profile)
    try:native,trace=prior(case)
    finally:sys.setprofile(previous)
    if pending:raise ValueError('Incomplete native body lifesteal observation')
    native['body_lifesteal']=events
    return native,trace
