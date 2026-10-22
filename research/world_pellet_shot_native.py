"""Observe real notify calls and final carriers without issuing buff queries."""
import sys
from calculator.buff_manager import BuffManager
from calculator import timeline
from world_frame_native import roster_names
from world_projectile_native import observe as projectile_observe


def observe(case):
    names=roster_names(case);notices=[];events=[];managers=[];errors=[];previous=sys.getprofile()
    notify_code=BuffManager.notify.__code__;fire_code=timeline.CharState._fire.__code__
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if event!='call' or frame.f_code is not notify_code:return
        try:
            local=frame.f_locals;caster=local['caster'];notice=local['event'];manager=local['self']
            if not managers:managers.append(manager)
            if caster!=names[case['contract']['owner']]:return
            if notice in ('pellet_hit','on_attack','hit_count') or notice.startswith('pellet_hit_in_shot:'):
                events.append(dict(event=notice,time=local['t']))
            if notice.startswith('pellet_hit_in_shot:'):
                caller=frame.f_back
                while caller is not None and caller.f_code is not fire_code:caller=caller.f_back
                if caller is None:raise ValueError('Per-shot notice outside auto fire')
                notices.append(dict(raw=notice.split(':',1)[1],owner=names.index(caster),time=local['t'],count=caller.f_locals['hit_count']))
        except (KeyError,ValueError,TypeError,AttributeError) as error:errors.append(str(error))
    sys.setprofile(profile)
    try:native,trace=projectile_observe(case)
    finally:sys.setprofile(previous)
    if errors:raise ValueError('Pellet shot native observation failed: '+str(errors))
    stacks={}
    if managers:
        for carrier in managers[0]._active:
            name=carrier.effect.get('name','')
            if name.startswith('shot-watch'):stacks[name]=carrier.stack
    native['pellet_shot']=dict(notices=notices,events=events,stacks=stacks)
    return native,trace
