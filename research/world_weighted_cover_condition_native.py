"""Passive original broken-cover heal observer on the same battle executor."""
from unittest.mock import patch
from contextlib import contextmanager
import engine_worker
from calculator.buff_manager import BuffManager
from world_weighted_battle_native import observe as original
@contextmanager
def capture():
    dispatch=BuffManager._dispatch_instant;receipts=[]
    def dispatched(manager,effect,caster,t,*args,**kwargs):
        selected=caster=='베이' and effect.get('stat')=='heal_hp_pct' and effect.get('trigger',{}).get('condition')==['not_self_cover_alive']
        if selected:before=manager.state['hp'][caster];cover=manager.state['cover_hp'][caster]
        answer=dispatch(manager,effect,caster,t,*args,**kwargs)
        if selected:receipts.append(dict(time=t,name=effect['name'],owner=caster,cover_hp=cover,hp_before=before,hp_after=manager.state['hp'][caster]))
        return answer
    with patch.object(BuffManager,'_dispatch_instant',dispatched):yield receipts
def observe(case):
    with capture() as receipts:native,trace=original(case)
    native['conditional_heals']=receipts;return native,trace
