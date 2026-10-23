"""Observe every original physical return packet, without inventing shot counts."""
from contextlib import contextmanager,nullcontext
from dataclasses import asdict
import sys
from unittest.mock import patch
import engine_worker
from calculator import timeline
import world_projectile_native as projectile
from world_focus_aim_native import observe as focus_observe
from portable_interrupt_runtime import capture_interrupt_landings
from world_frame_native import roster_names


@contextmanager
def capture_packet_sets(names):
    shots,sets,errors,pending=[],[],[],{}
    codes={getattr(timeline.CharState,k).__code__:k for k in ('_fire','_charge_fire')}
    previous=sys.getprofile()
    def profile(frame,event,answer):
        if previous is not None:previous(frame,event,answer)
        if frame.f_code not in codes:return
        values=frame.f_locals
        try:
            if event=='call':
                actor=values['self'];pending[id(frame)]=(names.index(actor.name),{'auto':0,'charge':1,'auto_warmup':2}[actor.fire_mode])
            elif event=='return':
                owner,mode=pending.pop(id(frame))
                if not answer:return
                split,count=values['split'],values['hit_count']
                assert type(split) is int and split>0 and count%split==0,'original physical split/count'
                assert answer is values['events'],'original returned packet identity'
                packets=[asdict(ev) for ev in answer]
                sets.append(dict(owner=owner,mode=mode,time=values['t'],pellets=split,muzzles=count//split,packets=packets))
                shots.append(dict(owner=owner,mode=mode,time=values['t'],pellets=split,muzzles=count//split,reach=max(ev.reach for ev in answer),damage=answer[0].damage))
        except (AssertionError,KeyError,ValueError,TypeError,AttributeError) as error:errors.append(type(error).__name__+': '+str(error))
    sys.setprofile(profile)
    try:
        yield shots,sets
        if errors or pending:raise ValueError('Original multi-packet observation failed: '+str(errors or 'unfinished physical frame'))
    finally:sys.setprofile(previous)


def observe(case):
    with capture_interrupt_landings() as receipts,capture_packet_sets(roster_names(case)) as (shots,sets),patch.object(projectile,'capture_projectile_shots',lambda names:nullcontext(shots)):
        native,trace=focus_observe(case)
    native['interrupt_landings']=[asdict(row) for row in receipts]
    native['physical_packet_sets']=sets
    return native,trace
