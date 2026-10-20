"""Observe actual impact/completion/heal order; never replay a CPU battle on GPU."""
import dataclasses
from contextlib import contextmanager
from unittest.mock import patch
from effect_runtime import state, pool
from impact_specs import ImpactTrace


def initialize(manager, capture):
    runtime=state(manager);runtime.counter_trace=[];runtime.impact_trace=ImpactTrace()
    capture['counter_uid_order']={};capture['counter_events']=[]
    original=manager.effect_runtime_prepare
    def prepare(effect,caster,t,carrier,initialized=False):
        ids=capture['counter_uid_order']
        if carrier.uid not in ids: ids[carrier.uid]=len(ids)+1
        return original(effect,caster,t,carrier,initialized)
    manager.effect_runtime_prepare=prepare


@contextmanager
def observe_events(capture,names):
    import impact_runtime
    from calculator.buff_manager import BuffManager
    original_impact=impact_runtime.publish_impact;original_notify=BuffManager.notify
    def hp(manager):return [manager.state['hp'][n] for n in names]
    def impact(manager,packet,t):
        capture['counter_events'].append(dict(event='impact_before',time=t,packet=dataclasses.asdict(packet),hp=hp(manager)))
        result=original_impact(manager,packet,t)
        capture['counter_events'].append(dict(event='impact_after',time=t,packet=dataclasses.asdict(packet),hp=hp(manager)))
        return result
    def notify(manager,event,t,caster,**ctx):
        watched=event=='event:heal_received' or event.startswith('event:target_counter_complete:')
        if watched:
            capture['counter_events'].append(dict(event=event,phase='before',time=t,owner=names.index(caster),hp=hp(manager)))
        result=original_notify(manager,event,t,caster,**ctx)
        if watched:
            capture['counter_events'].append(dict(event=event,phase='after',time=t,owner=names.index(caster),hp=hp(manager)))
        return result
    with patch.object(impact_runtime,'publish_impact',impact),patch.object(BuffManager,'notify',notify):yield


def before_finish(manager,capture,names):
    runtime=state(manager);ids=capture['counter_uid_order'];trace=[]
    for time,completion in runtime.counter_trace:
        row=dataclasses.asdict(completion);row['entry_ordinal']=ids[row.pop('uid')];row['time']=time;trace.append(row)
    resources=[]
    for record in pool(manager,'target_hit_counter').values():
        if not any(ab is record.carrier for ab in manager._active):continue
        resources.append(dict(entry_ordinal=ids[record.carrier.uid],epoch=record.epoch,name=record.carrier.effect['name'],owner=names.index(record.caster),actor=dataclasses.asdict(record.spec.actor),credit=record.credit,done=record.done,expires=record.expires))
    from world_actor_pool_native import actor_bindings
    boss=capture['boss'];parts=[]
    for b in actor_bindings(boss):
        if int(b.kind)!=1:continue
        run=boss._runs[b.run]
        if run.opens==0:continue
        target=run.targets[b.slot];parts.append(dict(identity=b.identity,generation=run.opens,extra_hits=target.extra_hits,extra_dealt=target.extra_dealt))
    return dict(epoch=runtime.counter_epoch,completions=trace,resources=resources,dead_actors=[dataclasses.asdict(a) for a in sorted(runtime.dead_actors,key=lambda a:(int(a.kind),a.identity,a.generation))],part_extra=parts,events=capture['counter_events'])
