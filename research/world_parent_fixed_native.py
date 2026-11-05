"""Actual parent context returns and full-charge notifications, with no extra reads."""
import sys
from contextlib import contextmanager
from unittest.mock import patch
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain

def observe(case):
    names=roster_names(case);previous=sys.getprofile();reads=[];notices=[];notify=BuffManager.notify;code=BuffManager.notify_ctx.__code__
    def profile(frame,event,value):
        if previous is not None:previous(frame,event,value)
        if event!='return' or frame.f_code is not code:return
        caller=frame.f_back
        if caller is None or caller.f_code.co_name!='_handle_damage_eff':return
        eff=caller.f_locals.get('eff',{})
        if eff.get('stat')=='dealt_fixed_damage':reads.append(dict(name=eff['name'],owner=names.index(caller.f_locals['caster']),time=caller.f_locals['t'],value=value))
    def notified(self,event,t,caster,**kw):
        if event=='full_charge_hit':notices.append(dict(owner=names.index(caster),time=t,dealt=kw.get('dealt')))
        return notify(self,event,t,caster,**kw)
    with patch.object(BuffManager,'notify',notified):
        sys.setprofile(profile)
        try:n,t=plain(case)
        finally:sys.setprofile(previous)
    n['parent_fixed']=dict(reads=reads,notices=notices,packets=t);return n,t
