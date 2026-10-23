"""Read actual shot/notify/instant calls; never inject or replay notifications."""
import sys
from calculator import timeline
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as original


def observe(case):
    names=roster_names(case);events=[];errors=[];previous=sys.getprofile()
    shot_code=timeline.CharState._charge_fire.__code__;notify_code=BuffManager.notify.__code__;instant_code=BuffManager._dispatch_instant.__code__
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if event!='call':return
        v=frame.f_locals
        try:
            if frame.f_code is shot_code:
                events.append(dict(kind='shot',owner=names.index(v['self'].name),time=v['t'],full=v['is_full']))
            elif frame.f_code is notify_code and v['event'] in ('squad_ammo_consume','on_attack','non_full_charge_fire','full_charge','full_charge_fire','hit_count','full_charge_hit'):
                events.append(dict(kind='notify',owner=names.index(v['caster']),time=v['t'],event=v['event']))
            elif frame.f_code is instant_code and v['effect'].get('name')=='nonfull-watch':
                events.append(dict(kind='activate',owner=names.index(v['caster']),time=v['t']))
        except (KeyError,ValueError,TypeError) as error:errors.append(str(error))
    sys.setprofile(profile)
    try:native,trace=original(case)
    finally:sys.setprofile(previous)
    if errors:raise ValueError('Non-full charge observation failed: '+str(errors))
    native['nonfull_charge']=events
    return native,trace
