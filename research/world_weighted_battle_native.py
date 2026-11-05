"""Reuse the complete original simulator and physical shot observer, CPU only."""
import copy,hashlib,json
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from portable_heavyarms_lock_cases import factory
from weighted_incoming_battle_model import weighted_incoming

def observe(case):
    before=copy.deepcopy(case);prepared=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True));captured={}
    registered=BuffManager._register_all;execute=engine_worker.sim.execute;notify=BuffManager.notify;notifications=[]
    def register(manager):
        answer=registered(manager)
        actual=[dict(effect=copy.deepcopy(e),owner=n) for e,n in manager._effects]
        if actual!=prepared['effects']:raise ValueError('Original weighted definitions/owners/order changed')
        captured['definitions']=len(actual)
        return answer
    def executed(run):
        if case.get('declared_burst_sequence'):
            from portable_declared_burst_sequence import apply
            from calculator import timeline
            expected=[{k:v for k,v in c.items() if k!='_weapon'} for c in prepared['chars']]
            if run.squad!=expected or run.config!=prepared['policies']['config'] or run.seed!=prepared['policies']['seed']:raise ValueError('Original squad/config/seed changed before declared sequence')
            result=timeline.simulate(run.squad,config=apply(run.config,prepared['chars'],case['declared_burst_sequence']),enemy=run.enemy,seed=run.seed,verbose=True)
        else:result=execute(run)
        captured['result']=result;return result
    def notified(manager,event,t,owner,*args,**kwargs):
        if event in ('received_hit','event:cover_hit'):notifications.append(dict(event=event,time=t,owner=owner))
        return notify(manager,event,t,owner,*args,**kwargs)
    baseline=None
    if case['contract']['scenario']=='inactive':
        with patch.object(engine_worker.sim,'execute',executed):baseline,baseline_trace=factory().native_reference(case['body'])
        baseline_hits=copy.deepcopy(captured['result'].squad_hits)
    with patch.object(BuffManager,'_register_all',register),patch.object(engine_worker.sim,'execute',executed),patch.object(BuffManager,'notify',notified),weighted_incoming(case['allocation'],case['names']) as data:
        native,trace=factory().native_reference(case['body'])
    result=captured['result']
    if baseline is not None and (native!=baseline or trace!=baseline_trace or result.squad_hits!=baseline_hits):raise ValueError('Inactive extension changed full original battle/trace/hits')
    native['hits']=[dict(time=h.t,pattern=h.pattern,owner=case['names'].index(h.target),damage=h.damage,pierce=h.pierce,shield=h.shield,cover=h.cover,decoy=h.decoy,hp=h.hp,hp_after=h.hp_after,down=h.down) for h in result.squad_hits]
    native['weighted_incoming']=data
    native['weighted_notifications']=notifications
    native['inactive_transparent']=baseline is not None
    native['original_input_identity']=dict(definitions=captured['definitions'],original_definitions_sha256=hashlib.sha256(json.dumps(prepared['effects'],sort_keys=True,ensure_ascii=False).encode()).hexdigest(),original_effects_and_owners_verified=True)
    if case!=before:raise ValueError('Weighted model changed original input')
    return native,trace
