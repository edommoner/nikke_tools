"""Observe actual recursion and capacity returns; never add a buff/provider query."""
import sys
from contextlib import contextmanager
from calculator import timeline
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain

@contextmanager
def capture(names):
    previous=sys.getprofile();reads=[];capacities=[];pending={}
    scale=BuffManager._scale_by_max_ammo.__code__;full=timeline.CharState._full_ammo.__code__
    def profile(frame,event,value):
        if previous is not None:previous(frame,event,value)
        if frame.f_code not in (scale,full) or event not in ('call','return'):return
        v=frame.f_locals
        if frame.f_code is scale:
            if event=='call':
                row=dict(owner=names.index(v['recipient']),time=v['t'],base=v['val'],recursive=v['recipient'] in v['self']._ammo_query)
                reads.append(row);pending[id(frame)]=row
            else:pending.pop(id(frame))['value']=value
        elif event=='return' and frame.f_back is not None and frame.f_back.f_code.co_name=='<lambda>':
            # Only returns to the installed max_ammo_provider, not unrelated reload calls.
            parent=frame.f_back.f_back
            if parent is not None and parent.f_code is scale:
                capacities.append(dict(owner=names.index(v['self'].name),time=v['t'],value=value,memo=v['self']._wc_ammo_full))
    sys.setprofile(profile)
    try:yield dict(reads=reads,capacities=capacities)
    finally:sys.setprofile(previous)
    if pending:raise ValueError('Incomplete maximum-ammunition observation')

def observe(case):
    with capture(roster_names(case)) as observation:n,t=plain(case)
    n['max_ammo_scaling']=observation
    return n,t
