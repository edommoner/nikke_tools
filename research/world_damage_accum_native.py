"""Observe actual installed accumulation calls/records; never add semantic queries."""
import sys
from contextlib import contextmanager,nullcontext
from unittest.mock import patch
import engine_worker,damage_accum_runtime
from calculator import timeline
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain
STATS=damage_accum_runtime.STATS

@contextmanager
def capture(names,*,tag_effects=False):
    previous=sys.getprofile();events=[];pending={};entries={};last=[None];data=dict(events=events)
    codes={BuffManager.accumulate_damage.__code__:'collect',BuffManager._accum_rate.__code__:'rate',BuffManager.accum_discharge.__code__:'take',damage_accum_runtime.activate.__code__:'snapshot'}
    def pools(manager):
        out=[]
        for ab in manager._active:
            if ab.effect.get('stat') not in STATS:continue
            entry=entries.setdefault(ab.uid,len(entries)+1)
            out.append(dict(entry=entry,row=ab.effect['_portable_observer_row'],owner=names.index(ab.caster),name=ab.effect.get('name',''),stat=ab.effect['stat'],base=ab.accum_cap,current=ab.accum,done=ab.accum_done,recipients=None if ab.target_chars is None else list(ab.target_chars)))
        return out
    def view(manager):return dict(pools=pools(manager),archive=dict(manager._accum_last))
    def profile(frame,event,value):
        if previous is not None:previous(frame,event,value)
        kind=codes.get(frame.f_code)
        if kind is None or event not in ('call','return'):return
        v=frame.f_locals;manager=v.get('self',v.get('manager'));last[0]=manager
        if kind=='snapshot' and (v['effect'].get('type')!='buff' or v['effect'].get('stat') not in STATS):return
        if event=='call':
            row=dict(kind=kind,time=v.get('t'),before=view(manager))
            if kind in ('snapshot','collect'):row['owner']=names.index(v['caster'])
            if kind=='snapshot':row['row']=v['effect']['_portable_observer_row']
            if kind=='collect':row['amount']=v['damage']
            if kind=='rate':row.update(entry=entries.setdefault(v['ab'].uid,len(entries)+1),row=v['ab'].effect['_portable_observer_row'])
            if kind=='take':
                row['name']=v['name'];caller=frame.f_back.f_locals;row['requester']=names.index(caller['caster']);row['row']=caller['eff']['_portable_observer_row']
            events.append(row);pending[id(frame)]=row
        else:
            row=pending.pop(id(frame));row.update(after=view(manager),returned_sequence=len(events))
            if kind in ('rate','take'):row['value']=value
            if kind=='collect':row['full']=[dict(name=n,owner=names.index(c)) for n,c in v.get('full',[])]
    original_notify=BuffManager.notify;original_hit=timeline.HitEvent
    def notify(manager,event,t,caster,*args,**kwargs):
        if event.startswith('event:accum_full:'):
            events.append(dict(kind='full-notice',name=event.removeprefix('event:accum_full:'),owner=names.index(caster),time=t,before=view(manager)))
        return original_notify(manager,event,t,caster,*args,**kwargs)
    def hit(*args,**kwargs):
        result=original_hit(*args,**kwargs)
        if result.hit_tag=='accum_split_damage':events.append(dict(kind='emission',time=result.t,owner=names.index(result.caster),amount=result.damage,name=result.skill_name,rule=result.rule,split=result.split,critical=result.is_crit))
        return result
    original_register=BuffManager._register_all;tagged={}
    def register(manager):
        result=original_register(manager)
        for index,(effect,_) in enumerate(manager._effects):
            tagged.setdefault(id(effect),(effect,'_portable_observer_row' in effect,effect.get('_portable_observer_row')))
            effect['_portable_observer_row']=index
        data['definitions']=[dict(owner=names.index(owner),name=e.get('name'),stat=e.get('stat'),kind=e.get('type')) for e,owner in manager._effects]
        return result
    with patch.object(BuffManager,'_register_all',register) if tag_effects else nullcontext(),patch.object(BuffManager,'notify',notify),patch.object(timeline,'HitEvent',hit):
        sys.setprofile(profile)
        try:yield data
        finally:
            sys.setprofile(previous)
            try:
                if not pending:data['final']=view(last[0]) if last[0] is not None else dict(pools=[],archive={})
            finally:
                for effect,present,value in tagged.values():
                    if present:effect['_portable_observer_row']=value
                    else:effect.pop('_portable_observer_row',None)
    if pending:raise ValueError('Incomplete damage-accumulation observation')

def observe(case):
    with capture(roster_names(case)) as data:n,t=plain(case)
    n['damage_accumulation']=data;return n,t
