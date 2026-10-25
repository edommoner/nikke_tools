"""Read real original gauge dispatches and final stored state, without querying stats."""
import copy
from contextlib import contextmanager
from unittest.mock import patch

@contextmanager
def capture(case):
    from calculator.buff_manager import BuffManager
    dispatch=BuffManager._dispatch_instant;register=BuffManager._register_all;notify=BuffManager.notify
    result=dict(dispatches=[],notifications=[],final={});managers=[]
    def registered(manager):
        value=register(manager);managers.append(manager);return value
    def observed(manager,effect,caster,t,*args,**kwargs):
        if effect.get('stat') not in ('gauge_charge','gauge_consume'):return dispatch(manager,effect,caster,t,*args,**kwargs)
        index=effect.get('_portable_observer_row')
        if type(index) is not int or not 0<=index<len(case['effects']) or case['effects'][index]['name']!=effect['name'] or case['names'][case['owners'][index]]!=caster:raise ValueError('Original gauge dispatch identity mismatch')
        row=dict(row=index,owner=case['names'].index(caster),time=t,stat=effect['stat'],resource=effect['gauge_id'],before=copy.deepcopy(manager.state.get('gauges',{})))
        value=dispatch(manager,effect,caster,t,*args,**kwargs);row['after']=copy.deepcopy(manager.state.get('gauges',{}));result['dispatches'].append(row);return value
    def notified(manager,event,t,caster,**kwargs):
        if event.startswith('every_stack:'):result['notifications'].append(dict(owner=case['names'].index(caster),resource=event.split(':',1)[1],time=t,boundary=kwargs['stack_value']))
        return notify(manager,event,t,caster,**kwargs)
    with patch.object(BuffManager,'_register_all',registered),patch.object(BuffManager,'_dispatch_instant',observed),patch.object(BuffManager,'notify',notified):yield result
    if len(managers)!=1:raise ValueError('One original gauge manager required')
    result['final']=copy.deepcopy(managers[0].state.get('gauges',{}))
