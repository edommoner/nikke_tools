"""Passive original stack operations; no recipient or stat queries."""
import math
from contextlib import contextmanager
from unittest.mock import patch
OPS={'buff_stack_add','buff_stack_remove','buff_stack_init','debuff_stack_add','debuff_stack_remove'}

def snapshot(manager,case):
    rows=[]
    for active in manager._active:
        effect=active.effect
        if effect.get('_boss_bound') or effect.get('type')!='buff' or effect.get('max_stack',1)==1:continue
        index=effect.get('_portable_observer_row')
        if type(index) is not int or not 0<=index<len(case['effects']) or effect['name']!=case['effects'][index]['name'] or case['names'][case['owners'][index]]!=active.caster:raise ValueError('Original stack carrier identity mismatch')
        rows.append(dict(row=index,owner=case['names'].index(active.caster),members=None if active.target_chars is None else list(active.target_chars),stack=active.stack,activated=active.activated_at,end=None if active.expires_at==math.inf else active.expires_at))
    return rows

@contextmanager
def capture(case):
    from calculator.buff_manager import BuffManager
    register=BuffManager._register_all;dispatch=BuffManager._dispatch_instant;maximum=BuffManager._apply_buff_max_stack_add;notify=BuffManager.notify
    result=dict(dispatches=[],notifications=[],final=[]);managers=[]
    def registered(manager):
        answer=register(manager);managers.append(manager);return answer
    def observe(handler,manager,effect,caster,t,*args,**kwargs):
        index=effect.get('_portable_observer_row')
        if type(index) is not int or not 0<=index<len(case['effects']) or effect['name']!=case['effects'][index]['name'] or case['names'][case['owners'][index]]!=caster:raise ValueError('Original stack dispatch identity mismatch')
        row=dict(row=index,owner=case['names'].index(caster),time=t,stat=effect['stat'],before=snapshot(manager,case),partial_skips_before=manager.partial_skips)
        answer=handler(manager,effect,caster,t,*args,**kwargs)
        row.update(after=snapshot(manager,case),partial_skips_after=manager.partial_skips);result['dispatches'].append(row);return answer
    def dispatched(manager,effect,caster,t,*args,**kwargs):
        if effect.get('stat') not in OPS:return dispatch(manager,effect,caster,t,*args,**kwargs)
        return observe(dispatch,manager,effect,caster,t,*args,**kwargs)
    def maximized(manager,effect,caster,t):return observe(maximum,manager,effect,caster,t)
    def notified(manager,event,t,caster,**kwargs):
        if event.startswith('stack_reach:'):result['notifications'].append(dict(owner=case['names'].index(caster),event=event,time=t))
        return notify(manager,event,t,caster,**kwargs)
    with patch.object(BuffManager,'_register_all',registered),patch.object(BuffManager,'_dispatch_instant',dispatched),patch.object(BuffManager,'_apply_buff_max_stack_add',maximized),patch.object(BuffManager,'notify',notified):yield result
    if len(managers)!=1:raise ValueError('One original stack manager required')
    result['final']=snapshot(managers[0],case)
