"""Observe actual native notify/activation order without extra state queries."""
import sys
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as native_observe

def observe(case):
    names=roster_names(case);events=[];previous=sys.getprofile();errors=[]
    def profile(frame,event,result):
        if previous is not None:previous(frame,event,result)
        if event!='call':return
        v=frame.f_locals
        try:
            if frame.f_code is BuffManager.notify.__code__ and (v['event'] in ('burst_cast','event:ally_burst_cast') or v['event'].startswith('squad_burst_cast:')):
                events.append(dict(kind='notify',event=v['event'],owner=names.index(v['caster']),time=v['t']))
            elif frame.f_code is BuffManager._dispatch_instant.__code__ and v['effect'].get('name','').startswith('listener-'):
                events.append(dict(kind='activate',owner=names.index(v['caster']),time=v['t']))
        except (KeyError,ValueError,TypeError) as error:errors.append(str(error))
    sys.setprofile(profile)
    try:native,trace=native_observe(case)
    finally:sys.setprofile(previous)
    if errors:raise ValueError('Native ally-burst observation failed: '+str(errors))
    native['ally_burst_events']=events
    return native,trace
