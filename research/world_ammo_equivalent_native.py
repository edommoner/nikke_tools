"""Read actual instant dispatches and squad notices; no extra state queries."""
import inspect,sys
from contextlib import contextmanager
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as projectile_observe


@contextmanager
def capture(case):
    names=roster_names(case);notices=[];calls=[];frames={};managers=[];previous=sys.getprofile();errors=[]
    notify=BuffManager.notify.__code__;dispatch=inspect.unwrap(BuffManager._dispatch_instant).__code__
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        try:
            if event=='call' and frame.f_code is notify and frame.f_locals['event']=='squad_ammo_consume':
                local=frame.f_locals
                if not managers:managers.append(local['self'])
                parent=frame.f_back;origin='physical'
                while parent is not None:
                    if parent.f_code is dispatch and parent.f_locals['eff'].get('stat')=='squad_ammo_consume_as':origin=parent.f_locals['eff']['name'];break
                    parent=parent.f_back
                notices.append(dict(owner=names.index(local['caster']),time=local['t'],origin=origin))
            elif frame.f_code is dispatch and frame.f_locals['eff'].get('stat')=='squad_ammo_consume_as':
                local=frame.f_locals
                if event=='call':
                    if not managers:managers.append(local['self'])
                    frames[id(frame)]=len(calls);calls.append(dict(name=local['eff']['name'],owner=names.index(local['caster']),time=local['t'],from_tick=local['from_tick']))
                elif event=='return':calls[frames.pop(id(frame))]['value']=local.get('val')
        except (KeyError,ValueError,TypeError,AttributeError) as error:errors.append(str(error))
    data=dict(notices=notices,calls=calls)
    sys.setprofile(profile)
    try:yield data
    finally:sys.setprofile(previous)
    if errors:raise ValueError('Ammo-equivalent observation failed: '+str(errors))
    manager=managers[0];stacks=[]
    for carrier in manager._active:
        if carrier.effect.get('name')=='ammo-watch':stacks.append(dict(owner=names.index(carrier.caster),stack=carrier.stack))
    data.update(stacks=stacks,squad_count=manager._event_counts.get('__squad__',{}).get('squad_ammo_consume',0))

def observe(case):
    with capture(case) as data:native,trace=projectile_observe(case)
    native['ammo_equivalent']=data
    return native,trace
