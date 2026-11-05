"""Read real original forced slots, duration mutations and their clocks."""
import math
from contextlib import contextmanager
from unittest.mock import patch

def identity(case,effect,caster):
    row=effect.get('_portable_observer_row')
    if type(row) is not int or not 0<=row<len(case['effects']) or effect['name']!=case['effects'][row]['name'] or caster!=case['names'][case['owners'][row]]:raise ValueError('Original source operation identity mismatch')
    return row

def clocks(manager):
    return [dict(row=e['_portable_observer_row'],due=manager._next_fire[id(e)][0],interval=manager._next_fire[id(e)][1]) for e,_ in manager._effects if id(e) in manager._next_fire]

def carriers(manager,case,selected):
    rows=[]
    for active in manager._active:
        effect=active.effect
        if effect.get('_boss_bound'):continue
        row=identity(case,effect,active.caster)
        if row not in selected:continue
        timer=manager._dot_timers.get(id(effect))
        rows.append(dict(row=row,owner=case['names'].index(active.caster),members=None if active.target_chars is None else list(active.target_chars),stack=active.stack,activated=active.activated_at,end=None if active.expires_at==math.inf else active.expires_at,dot=None if timer is None else dict(next=timer[1],expiry=timer[2])))
    return rows

@contextmanager
def capture(case):
    from calculator.buff_manager import BuffManager
    dispatch=BuffManager._dispatch_instant;activate=BuffManager._activate;register=BuffManager._register_all
    result=dict(dispatches=[],final=[]);pending=[];managers=[];selected=set()
    for effect in case['effects']:
        if effect.get('stat')=='named_buff_duration_extend':
            name=effect['target_effect'];selected.update(i for i,e in enumerate(case['effects']) if e.get('name','')==name or e.get('name','').startswith(name+' '))
    def registered(manager):
        answer=register(manager);managers.append(manager);return answer
    def activated(manager,effect,caster,t,*args,**kwargs):
        if pending and pending[-1]['stat']=='force_skill_use':
            row=identity(case,effect,caster);selected.add(row);pending[-1]['actual_activations'].append(dict(row=row,owner=case['names'].index(caster),time=t,source=effect['source']))
        return activate(manager,effect,caster,t,*args,**kwargs)
    def dispatched(manager,effect,caster,t,*args,**kwargs):
        if effect.get('stat') not in ('force_skill_use','named_buff_duration_extend'):return dispatch(manager,effect,caster,t,*args,**kwargs)
        row=dict(row=identity(case,effect,caster),owner=case['names'].index(caster),time=t,stat=effect['stat'],before=carriers(manager,case,selected),before_clocks=clocks(manager),actual_activations=[])
        pending.append(row)
        try:value=dispatch(manager,effect,caster,t,*args,**kwargs)
        finally:assert pending.pop() is row
        row.update(after=carriers(manager,case,selected),after_clocks=clocks(manager));result['dispatches'].append(row);return value
    with patch.object(BuffManager,'_register_all',registered),patch.object(BuffManager,'_dispatch_instant',dispatched),patch.object(BuffManager,'_activate',activated):yield result
    if len(managers)!=1 or pending:raise ValueError('One completed original source manager required')
    result.update(selected_rows=sorted(selected),final=carriers(managers[0],case,selected),final_clocks=clocks(managers[0]))
