"""Passively read owned source records, actual refreshes and tick callbacks."""
import math
from contextlib import contextmanager
from unittest.mock import patch
from world_original_source_native import identity

@contextmanager
def capture(case):
    from calculator.buff_manager import BuffManager
    dispatch=BuffManager._dispatch_instant;notify=BuffManager.notify;register=BuffManager._register_all
    data=dict(dispatches=[],ticks=[]);managers=[];last={}
    def records(manager):
        state=getattr(manager,'_effect_runtime_state',None)
        pool={} if state is None else state.resources.get('periodic_sources',{})
        rows=[]
        for (caster,name),record in pool.items():
            row,refreshed=last[(caster,name)]
            rows.append(dict(owner=case['names'].index(caster),name=name,row=row,refreshed=refreshed,epoch=record.epoch,legacy=record.spec.legacy,expiry=[None if e==math.inf else e for e in record.expiry],next_at=record.next_at))
        return rows
    def registered(manager):
        result=register(manager);managers.append(manager);return result
    def dispatched(manager,effect,caster,t,*args,**kwargs):
        if effect.get('stat') not in ('feather_refresh','periodic_source_refresh'):return dispatch(manager,effect,caster,t,*args,**kwargs)
        row=identity(case,effect,caster);before=records(manager);result=dispatch(manager,effect,caster,t,*args,**kwargs)
        from periodic_source_specs import specification
        spec=specification(effect);last[(caster,spec.name)]=(row,t)
        data['dispatches'].append(dict(row=row,owner=case['names'].index(caster),time=t,before=before,after=records(manager)))
        return result
    def notified(manager,event,t,caster,*args,**kwargs):
        if event=='feather_tick' or event.startswith('source_tick:'):data['ticks'].append(dict(owner=case['names'].index(caster),event=event,time=t,sources=records(manager)))
        return notify(manager,event,t,caster,*args,**kwargs)
    with patch.object(BuffManager,'_register_all',registered),patch.object(BuffManager,'_dispatch_instant',dispatched),patch.object(BuffManager,'notify',notified):yield data
    if len(managers)!=1:raise ValueError('One completed original source manager required')
    data['final']=records(managers[0]);data['model_warnings']=list(managers[0]._effect_runtime_state.model_warnings)
