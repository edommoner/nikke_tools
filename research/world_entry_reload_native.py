"""Observe actual native mode ticks/reload queries; never issue a stat query."""
import copy,math
from contextlib import contextmanager
from unittest.mock import patch
from calculator import timeline
from world_frame_native import roster_names
from world_projectile_native import observe as projectile_native


@contextmanager
def data_context(case):
    names=roster_names(case);replacement=copy.deepcopy(timeline._DELAYS.get('_weapon_change',{}))
    for row in case.get('entry_delays',[]):
        value=row['value'];owner=row['owner']
        if type(owner) is not int or not 0<=owner<5 or type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=180:raise ValueError('Invalid literal mode entry delay')
        replacement.setdefault(names[owner],{}).setdefault(row['name'],{})['entry_delay']=value
    with patch.dict(timeline._DELAYS,{'_weapon_change':replacement}):yield


def observe(case):
    names=roster_names(case);frames=[];queries=[];current=[];entries=[]
    tick=timeline.CharState._tick_weapon_change;duration=timeline.CharState._reload_duration
    begin=timeline.CharState.begin_weapon_session
    def state(actor):
        return dict(entry_until=actor._wc_entry_reload_until,new_session=actor._wc_new_session,ammo=actor.ammo,phase=actor._charge_phase,charge_start=actor._charge_start_t,reload_until=actor.reloading_until)
    def queried(actor,bm,t):
        before=state(actor);base_reload=actor.weapon['reload_time']
        result=duration(actor,bm,t)
        if current:queries.append(dict(frame=current[-1],owner=names.index(actor.name),time=t,base_reload=base_reload,result=result,before=before))
        return result
    def entered(actor,bm,t):
        row=dict(owner=names.index(actor.name),time=t,before=state(actor))
        answer=begin(actor,bm,t);row['after']=state(actor);entries.append(row);return answer
    def ticked(actor,t,bm,enemy,cfg,effect):
        index=len(frames);row=dict(owner=names.index(actor.name),time=t,name=effect.get('name'),entry_reload=bool(effect.get('entry_reload')),before=state(actor))
        frames.append(row);current.append(index)
        try:
            answer=tick(actor,t,bm,enemy,cfg,effect);row.update(after=state(actor),hits=len(answer));return answer
        finally:current.pop()
    with data_context(case),patch.object(timeline.CharState,'_tick_weapon_change',ticked),patch.object(timeline.CharState,'_reload_duration',queried),patch.object(timeline.CharState,'begin_weapon_session',entered):
        native,trace=projectile_native(case)
    native['entry_reload']=dict(frames=frames,queries=queries,entries=entries)
    return native,trace
