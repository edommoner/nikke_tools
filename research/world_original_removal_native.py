"""Observe actual original named-removal calls without changing their inputs."""
from contextlib import contextmanager
from unittest.mock import patch

@contextmanager
def capture():
    from calculator.buff_manager import BuffManager
    original=BuffManager._dispatch_instant;rows=[]
    def dispatched(manager,eff,caster,t,*args,**kwargs):
        if eff.get('stat')!='remove_named_buff':return original(manager,eff,caster,t,*args,**kwargs)
        target=eff['target_effect'];count=lambda:sum(ab.effect.get('name')==target for ab in manager._active)
        row=dict(row=eff['_portable_observer_row'],owner=caster,time=t,target=target,before=count())
        result=original(manager,eff,caster,t,*args,**kwargs)
        row['after']=count();rows.append(row);return result
    with patch.object(BuffManager,'_dispatch_instant',dispatched):yield rows
