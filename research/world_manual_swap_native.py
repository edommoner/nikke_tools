"""Observe existing ready/start/finish calls, without additional buff queries."""
import copy,inspect,sys
from contextlib import contextmanager
from unittest.mock import patch
from calculator import timeline
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as projectile_observe


@contextmanager
def data_context(case):
    names=roster_names(case);flags=case.get('manual_swap',[False]*5)
    if not isinstance(flags,list) or len(flags)!=5 or any(type(v) is not bool for v in flags):raise ValueError('Five literal manual-swap flags required')
    original=timeline.CharState.__init__
    def initialized(actor,char,*args,**kwargs):
        # This is authored character input, passed before the native constructor.
        return original(actor,dict(copy.deepcopy(char),weapon_mode_swap=flags[names.index(char['name'])]),*args,**kwargs)
    with patch.object(timeline.CharState,'__init__',initialized):yield


def observe(case):
    names=roster_names(case);ready=[];conditions=[];ticks=[];stack=[]
    original=BuffManager.manual_swap_ready;tick=timeline.CharState.tick
    condition=inspect.unwrap(BuffManager._condition_ok).__code__;previous=sys.getprofile()
    def profiled(frame,event,arg):
        if previous is not None:previous(frame,event,arg)
        if stack and event=='return' and frame.f_code is condition:
            local=frame.f_locals;conditions.append(dict(query=stack[-1],name=local.get('eff',{}).get('name'),result=bool(arg)))
    def queried(bm,caster,t):
        index=len(ready);row=dict(owner=names.index(caster),time=t);ready.append(row);stack.append(index)
        try:row['result']=original(bm,caster,t);return row['result']
        finally:stack.pop()
    def state(actor):return dict(ammo=actor.ammo,reload_until=actor.reloading_until,post_reload_until=actor._post_reload_end_t,phase=actor._charge_phase,charge_start=actor._charge_start_t,in_mode=actor._in_weapon_change,sequence_index=actor._ctrl_seq_i)
    def ticked(actor,t,bm,*args,**kwargs):
        row=dict(owner=names.index(actor.name),time=t,before=state(actor));answer=tick(actor,t,bm,*args,**kwargs);row.update(after=state(actor),hits=len(answer));ticks.append(row);return answer
    sys.setprofile(profiled)
    try:
        with data_context(case),patch.object(BuffManager,'manual_swap_ready',queried),patch.object(timeline.CharState,'tick',ticked):native,trace=projectile_observe(case)
    finally:sys.setprofile(previous)
    native['manual_swap']=dict(queries=ready,conditions=conditions,ticks=ticks)
    return native,trace
