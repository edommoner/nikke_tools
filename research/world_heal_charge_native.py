"""Observe existing pool lifecycle returns and fields without extra semantic queries."""
import sys
from contextlib import contextmanager,nullcontext
from unittest.mock import patch
from calculator.buff_manager import BuffManager
import engine_worker,heal_charge_compat as charge
from world_frame_native import roster_names
from world_projectile_native import observe as plain

@contextmanager
def capture(names,*,record_final=False,tag_effects=False):
    previous=sys.getprofile();events=[];pending={};last_manager=[None];observation=dict(events=events)
    codes={getattr(charge,k).__code__:k for k in ('snapshot','capacity','collect','take','latch_end','discharge','discard_removed')}
    def pools(manager):
        active={a.uid for a in manager._active}
        return [dict(row=a.effect['_portable_observer_row'],owner=names.index(a.caster),base=a.heal_charge_base_cap,current=a.heal_charge_current,done=a.heal_charge_done,ended=a.heal_charge_ended,active=a.uid in active) for a in getattr(manager,'_heal_charge_records',{}).values()]
    def profile(frame,event,value):
        if previous is not None:previous(frame,event,value)
        kind=codes.get(frame.f_code)
        if kind is None or event not in ('call','return'):return
        v=frame.f_locals;manager=v['self'];last_manager[0]=manager
        if kind=='snapshot' and (v['eff'].get('type')!='buff' or v['eff'].get('stat')!=charge.STAT):return
        if event=='call':
            row=dict(kind=kind,time=v.get('t'),before=pools(manager))
            if kind in ('collect','take','latch_end'):row.update(name=v.get('name'),owner=names.index(v['caster']) if 'caster' in v else names.index(v['name']),amount=v.get('amount'))
            if kind in ('snapshot','discharge'):row.update(owner=names.index(v['caster']),row=v['eff']['_portable_observer_row'])
            if kind=='take':row['row']=frame.f_back.f_locals['eff']['_portable_observer_row']
            events.append(row);pending[id(frame)]=row
        else:
            row=pending.pop(id(frame));row.update(after=pools(manager),returned_sequence=len(events))
            if kind in ('take','capacity'):row['value']=value
            if kind=='capacity':row['row']=v['ab'].effect['_portable_observer_row']
            if kind=='discharge':row.update(returned_sequence=len(events),targets=[names.index(n) for n in v['targets']],taken=v['amount'])
    original_register=BuffManager._register_all
    def register(manager):
        result=original_register(manager)
        for index,(effect,_) in enumerate(manager._effects):effect['_portable_observer_row']=index
        observation['definitions']=[dict(owner=names.index(owner),name=e.get('name'),stat=e.get('stat'),kind=e.get('type')) for e,owner in manager._effects]
        return result
    with patch.object(BuffManager,'_register_all',register) if tag_effects else nullcontext():
        sys.setprofile(profile)
        try:yield observation
        finally:sys.setprofile(previous)
    if pending:raise ValueError('Incomplete healing-charge observation')
    if record_final:observation['final']=pools(last_manager[0]) if last_manager[0] is not None else []

def observe(case):
    with capture(roster_names(case)) as observation:n,t=plain(case)
    n['healing_charge']=observation;return n,t

def observe_extended(case):
    with capture(roster_names(case),record_final=True) as observation:n,t=plain(case)
    n['healing_charge']=observation;return n,t
