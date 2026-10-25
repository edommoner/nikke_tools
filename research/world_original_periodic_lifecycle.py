"""Read real original periodic activations and carrier refresh/retirement state."""
from contextlib import contextmanager
from unittest.mock import patch
from world_effect_identity import row as source_row
@contextmanager
def capture(case):
    from calculator.buff_manager import BuffManager
    original=BuffManager._activate;records=[]
    def snapshot(manager,name):
        return [dict(row=source_row(case,a.effect,a.caster),owner=case['names'].index(a.caster),targets=None if a.target_chars is None else list(a.target_chars),activated=a.activated_at,expires=a.expires_at,stack=a.stack,
                     timer=None if id(a.effect) not in manager._dot_timers else list(manager._dot_timers[id(a.effect)][1:]))
                for a in manager._active if a.effect.get('type')=='damage' and a.effect.get('tick_interval') and a.effect.get('name')==name]
    def activated(manager,effect,caster,t,*args,**kwargs):
        if effect.get('type')!='damage' or not effect.get('tick_interval'):return original(manager,effect,caster,t,*args,**kwargs)
        row=dict(row=source_row(case,effect,caster),owner=case['names'].index(caster),time=t,before=snapshot(manager,effect['name']))
        result=original(manager,effect,caster,t,*args,**kwargs)
        row['after']=snapshot(manager,effect['name']);records.append(row);return result
    with patch.object(BuffManager,'_activate',activated):yield records
