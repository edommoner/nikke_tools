"""Observe actual cover revival calls and stored quantities; never resolve again."""
from contextlib import contextmanager
from unittest.mock import patch
from world_original_source_native import identity

def cover_state(manager):
    return dict(current=dict(manager.state.get('cover_hp',{})),maximum=dict(manager.state.get('cover_max_hp',{})))

@contextmanager
def capture(case):
    from calculator.buff_manager import BuffManager
    register=BuffManager._register_all;dispatch=BuffManager._dispatch_instant;revive=BuffManager.revive_cover
    managers=[];pending=[];observed=dict(requests=[],deliveries=[])
    def registered(self):answer=register(self);managers.append(self);return answer
    def dispatched(self,eff,caster,t,*args,**kwargs):
        if eff.get('stat')!='cover_revive':return dispatch(self,eff,caster,t,*args,**kwargs)
        event=dict(row=identity(case,eff,caster),owner=case['names'].index(caster),time=t,before=cover_state(self),deliveries=[]);pending.append(event)
        try:answer=dispatch(self,eff,caster,t,*args,**kwargs)
        finally:assert pending.pop() is event
        event['after']=cover_state(self);observed['requests'].append(event);return answer
    def revived(self,name,hp):
        assert pending,'Every actual cover revival must belong to an original request'
        event=dict(target=case['names'].index(name),time=pending[-1]['time'],hp=hp,before=cover_state(self));answer=revive(self,name,hp);event['after']=cover_state(self);pending[-1]['deliveries'].append(event);observed['deliveries'].append(event);return answer
    with patch.object(BuffManager,'_register_all',registered),patch.object(BuffManager,'_dispatch_instant',dispatched),patch.object(BuffManager,'revive_cover',revived):yield observed
    assert len(managers)==1 and not pending,'One completed original cover manager required'
    for active in managers[0]._active:
        if active.effect.get('stat')=='atk_caster_based_pct' and active.effect.get('target','').startswith('allies_random:'):
            assert active.target_chars is None,'Native late random numeric rows must remain unresolved'
    observed['final']=cover_state(managers[0])
