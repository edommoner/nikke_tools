"""Observe actual dispatch mutations and state-end notifications without new queries."""
from contextlib import contextmanager
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_named_enemy_native import capture as capture_selection
from world_projectile_native import observe as plain

@contextmanager
def capture(names):
    dispatch=BuffManager._dispatch_instant;notify=BuffManager.notify;calls=[];events=[];depth=0
    def snapshot(bm,name):
        return [dict(owner=names.index(ab.caster),members=list(ab.target_chars or [])) for ab in bm._active if ab.effect.get('name')==name]
    def notified(bm,event,t,caster,**ctx):
        if depth and event.startswith('event:state_end:'):
            name=event[len('event:state_end:'):];events.append(dict(event=event,time=t,owner=names.index(caster),remaining=snapshot(bm,name)))
        return notify(bm,event,t,caster,**ctx)
    def dispatched(bm,eff,caster,t,from_tick=False):
        nonlocal depth
        if eff.get('stat')!='remove_named_buff' or not str(eff.get('target','')).startswith('enemies_with_buff:'):return dispatch(bm,eff,caster,t,from_tick=from_tick)
        name=eff['target_effect'];row=dict(time=t,owner=names.index(caster),before=snapshot(bm,name));start=len(events);depth+=1
        try:result=dispatch(bm,eff,caster,t,from_tick=from_tick)
        finally:depth-=1
        row.update(after=snapshot(bm,name),events=events[start:]);calls.append(row);return result
    with patch.object(BuffManager,'_dispatch_instant',dispatched),patch.object(BuffManager,'notify',notified):yield calls

def observe(case):
    names=roster_names(case)
    with capture_selection(names) as selection,capture(names) as removals:n,t=plain(case)
    n['named_enemy_removal']=dict(selection=selection,removals=removals);return n,t
