"""Observe logical marker lifecycle; dedicated Lock On targeting remains a gap."""
import copy,math
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from portable_heavyarms_lock_cases import factory,source_definitions
MARK='록 온'

def observe(case):
    body=case['body'];before=copy.deepcopy(body);source=factory()
    definitions=source_definitions()
    prepared=engine_worker.evaluate(dict(body,_portable_static_inputs=True))
    events=[];queries=[];probing=False;activate=BuffManager._activate;dispatch=BuffManager._dispatch_instant;named_state=BuffManager.enemy_has_state
    def snapshot(manager):
        nonlocal probing
        carriers=[dict(caster=a.caster,targets=list(a.target_chars or []),stack=a.stack,expires='infinite' if math.isinf(a.expires_at) else a.expires_at) for a in manager._active if a.effect.get('name')==MARK]
        # Keep explicit probes separate from natural selector callbacks.
        previous=probing;probing=True
        try:return dict(carriers=carriers,diagnostic_queries=dict(any_enemy=manager._has_target_state(MARK),boss=manager.enemy_has_state('__enemy__',MARK),stack=manager._target_stack(MARK)))
        finally:probing=previous
    def queried(manager,enemy,name):
        answer=named_state(manager,enemy,name)
        if not probing and name==MARK:queries.append(dict(target=enemy,name=name,present=answer))
        return answer
    def activated(manager,effect,caster,t,*args,**kwargs):
        answer=activate(manager,effect,caster,t,*args,**kwargs)
        if effect.get('stat')=='lock_on':events.append(dict(kind='activate',time=t,name=effect.get('name'),state=snapshot(manager)))
        return answer
    def dispatched(manager,effect,caster,t,*args,**kwargs):
        selected=effect.get('stat')=='remove_named_buff' and effect.get('target_effect')==MARK
        old=snapshot(manager) if selected else None
        answer=dispatch(manager,effect,caster,t,*args,**kwargs)
        if selected:events.append(dict(kind='remove',time=t,name=effect.get('name'),before=old,state=snapshot(manager)))
        return answer
    with patch.object(BuffManager,'_activate',activated),patch.object(BuffManager,'_dispatch_instant',dispatched),patch.object(BuffManager,'enemy_has_state',queried):native,trace=source.native_reference(body)
    baseline,baseline_trace=source.native_reference(body)
    if body!=before or native!=baseline or trace!=baseline_trace:raise AssertionError('Diagnostic marker probes changed complete native result/shot trace/input')
    native=dict(native,heavyarms_lock=dict(original_definitions=definitions,prepared_effect_count=len(prepared['effects']),events=events,natural_queries=queries,transparent=True,probe_queries_are_injected=True,spatial_selection_verified=False,target_count_extension_verified=False,full25_typed_projectile_verified=False))
    return native,trace
