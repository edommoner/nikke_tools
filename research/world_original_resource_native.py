"""Read real original gauge dispatches and final stored state, without querying stats."""
import copy
from contextlib import contextmanager
from unittest.mock import patch

@contextmanager
def capture(case,*,include_ammo=False):
    from calculator.buff_manager import BuffManager
    dispatch=BuffManager._dispatch_instant;register=BuffManager._register_all;notify=BuffManager.notify
    result=dict(dispatches=[],notifications=[],final={});managers=[]
    active_ammo=[]
    if include_ammo:result['ordered_notifications']=[]
    def registered(manager):
        value=register(manager);managers.append(manager);return value
    def observed(manager,effect,caster,t,*args,**kwargs):
        if effect.get('stat') not in (('gauge_charge','gauge_consume','gauge_consume_as_ammo') if include_ammo else ('gauge_charge','gauge_consume')):return dispatch(manager,effect,caster,t,*args,**kwargs)
        index=effect.get('_portable_observer_row')
        if type(index) is not int or not 0<=index<len(case['effects']) or case['effects'][index]['name']!=effect['name'] or case['names'][case['owners'][index]]!=caster:raise ValueError('Original gauge dispatch identity mismatch')
        row=dict(row=index,owner=case['names'].index(caster),time=t,stat=effect['stat'],resource=effect['gauge_id'],before=copy.deepcopy(manager.state.get('gauges',{})))
        ammo=effect.get('stat')=='gauge_consume_as_ammo'
        if ammo:active_ammo.append(effect['gauge_id'])
        try:value=dispatch(manager,effect,caster,t,*args,**kwargs)
        finally:
            if ammo:active_ammo.pop()
        row['after']=copy.deepcopy(manager.state.get('gauges',{}));result['dispatches'].append(row);return value
    def notified(manager,event,t,caster,**kwargs):
        if event.startswith('every_stack:'):
            row=dict(owner=case['names'].index(caster),resource=event.split(':',1)[1],time=t,boundary=kwargs['stack_value']);result['notifications'].append(row)
            if include_ammo:result['ordered_notifications'].append(dict(event=30,**row))
        elif include_ammo and event=='squad_ammo_consume' and active_ammo:
            result['ordered_notifications'].append(dict(event=26,owner=case['names'].index(caster),resource=active_ammo[-1],time=t,boundary=1.0))
        return notify(manager,event,t,caster,**kwargs)
    with patch.object(BuffManager,'_register_all',registered),patch.object(BuffManager,'_dispatch_instant',observed),patch.object(BuffManager,'notify',notified):yield result
    if len(managers)!=1:raise ValueError('One original gauge manager required')
    result['final']=copy.deepcopy(managers[0].state.get('gauges',{}))
