"""Read the new capacity model on actual buff activation and shot-consumption events."""
import copy
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from effect_target_count_policy import query,MODEL,STAT
from portable_heavyarms_lock_cases import factory,source_definitions,NAME

def observe(case):
    body=case['body'];before=copy.deepcopy(body);source=factory();events=[]
    prepared=engine_worker.evaluate(dict(body,_portable_static_inputs=True))
    activate=BuffManager._activate;consume=BuffManager.consume_bullet_buffs
    def read(manager,t):return query(manager,NAME,'록 온',t,base_count=5,capacity_limit=128,model=MODEL)
    def activated(manager,effect,caster,t,*args,**kwargs):
        answer=activate(manager,effect,caster,t,*args,**kwargs)
        if effect.get('stat')==STAT and caster==NAME:
            events.append(dict(kind='activate',time=t,query=read(manager,t)))
        return answer
    def consumed(manager,caster,t=0.):
        if caster!=NAME:return consume(manager,caster,t)
        previous=read(manager,t);answer=consume(manager,caster,t)
        events.append(dict(kind='consume',time=t,before=previous,query=read(manager,t)))
        return answer
    with patch.object(BuffManager,'_activate',activated),patch.object(BuffManager,'consume_bullet_buffs',consumed):
        native,trace=source.native_reference(body)
    baseline,baseline_trace=source.native_reference(body)
    if body!=before or native!=baseline or trace!=baseline_trace:
        raise AssertionError('Target-count queries changed complete native result/shot trace/input')
    native=dict(native,effect_target_count=dict(model=MODEL,original_definitions=source_definitions(),
        prepared_effect_count=len(prepared['effects']),events=events,transparent=True,
        selection_consumer_connected=False,gpu_supported=False))
    return native,trace
