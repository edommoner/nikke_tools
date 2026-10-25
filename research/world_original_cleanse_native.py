"""Passively read original cleanse calls and stored carrier membership."""
import math
from contextlib import contextmanager
from unittest.mock import patch

def snapshot(manager,case):
    rows=[]
    for active in manager._active:
        effect=active.effect
        if effect.get('_boss_bound') or not effect.get('polarity','').startswith('harmful'):continue
        index=effect.get('_portable_observer_row')
        if type(index) is not int or not 0<=index<len(case['effects']) or case['effects'][index]['name']!=effect['name'] or case['names'][case['owners'][index]]!=active.caster:raise ValueError('Original harmful carrier identity mismatch')
        rows.append(dict(row=index,owner=case['names'].index(active.caster),members=None if active.target_chars is None else list(active.target_chars),stack=active.stack,activated=active.activated_at,end=None if active.expires_at==math.inf else active.expires_at))
    return rows

@contextmanager
def capture(case):
    from calculator.buff_manager import BuffManager
    register=BuffManager._register_all;dispatch=BuffManager._dispatch_instant
    result=dict(dispatches=[],final=[]);managers=[];pending=[]
    def registered(manager):
        answer=register(manager);managers.append(manager);return answer
    def dispatched(manager,effect,caster,t,*args,**kwargs):
        if effect.get('stat') not in ('debuff_cleanse','enemy_buff_cleanse'):return dispatch(manager,effect,caster,t,*args,**kwargs)
        index=effect.get('_portable_observer_row')
        if type(index) is not int or not 0<=index<len(case['effects']) or case['effects'][index]['name']!=effect['name'] or case['names'][case['owners'][index]]!=caster:raise ValueError('Original cleanse dispatch identity mismatch')
        row=dict(row=index,owner=case['names'].index(caster),time=t,stat=effect['stat'],before=snapshot(manager,case));pending.append(row)
        try:answer=dispatch(manager,effect,caster,t,*args,**kwargs)
        finally:assert pending.pop() is row
        row['after']=snapshot(manager,case);result['dispatches'].append(row);return answer
    with patch.object(BuffManager,'_register_all',registered),patch.object(BuffManager,'_dispatch_instant',dispatched):yield result
    if len(managers)!=1 or pending:raise ValueError('One completed original cleanse manager required')
    result['final']=snapshot(managers[0],case)
