"""Read actual shield/decoy storage and heal deliveries; never resolve again."""
from contextlib import contextmanager
from unittest.mock import patch
from world_original_source_native import identity

def protections(manager,case,kind='shield'):
    if kind not in ('shield','decoy'):raise ValueError('Unknown protection kind')
    stats=('shield_from_max_hp_pct','shared_shield_from_max_hp_pct') if kind=='shield' else ('decoy',)
    rows=[]
    for active in manager._active:
        if active.effect.get('stat') not in stats:continue
        row=identity(case,active.effect,active.caster)
        rows.append(dict(row=row,owner=case['names'].index(active.caster),members=None if active.target_chars is None else list(active.target_chars),stack=active.stack,activated=active.activated_at,end=None if active.expires_at==float('inf') else active.expires_at,current=dict(getattr(active,kind+'_per_target')),capacity=dict(getattr(active,kind+'_max_per_target'))))
    return rows

def shields(manager,case):return protections(manager,case)

@contextmanager
def capture(case,*,kind='shield'):
    from calculator.buff_manager import BuffManager
    if kind not in ('shield','decoy'):raise ValueError('Unknown protection kind')
    stat=kind+'_heal_pct';method='heal_'+kind;storage=lambda manager,case:protections(manager,case,kind)
    dispatch=BuffManager._dispatch_instant;heal=getattr(BuffManager,method);register=BuffManager._register_all
    managers=[];pending=[];result=dict(requests=[],deliveries=[])
    def registered(self):answer=register(self);managers.append(self);return answer
    def dispatched(self,eff,caster,t,*args,**kwargs):
        if eff.get('stat')!=stat:return dispatch(self,eff,caster,t,*args,**kwargs)
        event=dict(row=identity(case,eff,caster),owner=case['names'].index(caster),time=t,from_tick=bool(kwargs.get('from_tick',args[0] if args else False)),before=storage(self,case),deliveries=[]);pending.append(event)
        try:answer=dispatch(self,eff,caster,t,*args,**kwargs)
        finally:assert pending.pop() is event
        event['after']=storage(self,case);result['requests'].append(event);return answer
    def healed(self,name,amount,t):
        before=storage(self,case);answer=heal(self,name,amount,t);event=dict(target=case['names'].index(name),time=t,amount=amount,healed=answer,before=before,after=storage(self,case))
        assert pending,'Every shield-heal call must belong to an observed original request'
        pending[-1]['deliveries'].append(event);result['deliveries'].append(event);return answer
    with patch.object(BuffManager,'_register_all',registered),patch.object(BuffManager,'_dispatch_instant',dispatched),patch.object(BuffManager,method,healed):yield result
    assert len(managers)==1 and not pending,'One completed original shield manager required'
    manager=managers[0];result['final']=storage(manager,case)
    result['clocks']=[dict(row=e['_portable_observer_row'],owner=case['names'].index(owner),next=manager._instant_timers[id(e)][1],expiry=None if manager._instant_timers[id(e)][2]==float('inf') else manager._instant_timers[id(e)][2]) for e,owner in manager._effects if e.get('stat')==stat and id(e) in manager._instant_timers]
