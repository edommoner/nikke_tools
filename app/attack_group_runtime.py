"""Collect distinct typed targets, then detach before synchronous callbacks.

Only explicitly opened groups participate. Existing impacts with identity zero
remain ordinary impacts until world/weapon producers supply real boundaries.
"""
from contextlib import contextmanager
from dataclasses import dataclass,field
from functools import wraps
from effect_runtime import CATALOG,Handler,pool,state
from impact_specs import HitOutcome
from attack_group_specs import AttackKey,AttackTargets,actor_policy,listener_plan,checked_time,MAX_GROUPS,MAX_TARGETS

@dataclass(eq=False)
class Group:
    key:AttackKey
    kinds:frozenset
    listeners:tuple
    opened:float
    targets:dict=field(default_factory=dict)
    closed:bool=False

@dataclass(frozen=True,eq=False)
class SealedGroup:
    result:AttackTargets
    listeners:tuple
    sealed:float

def plan(manager,caster):
    runtime=state(manager);cache=getattr(runtime,'attack_group_plans',None)
    if cache is None or cache[0] is not manager._effects:
        cache=(manager._effects,{})
        runtime.attack_group_plans=cache
    result=cache[1].get(caster)
    if result is None:
        result=listener_plan(manager._effects,caster);cache[1][caster]=result
    return result

def begin(manager,caster,identity,t,*,kinds):
    checked_time(t)
    runtime=state(manager);groups=pool(manager,'attack_groups')
    epoch=getattr(runtime,'attack_group_epoch',0)+1;key=AttackKey(caster,identity,epoch)
    policy=actor_policy(kinds);listeners=plan(manager,caster)
    if (caster,identity) in groups:raise ValueError('Attack group is already open')
    if sum(len(pool(manager,name)) for name in ('attack_groups','sealed_attack_groups','dispatching_attack_groups'))>=MAX_GROUPS:raise ValueError('Attack group capacity exceeded')
    frame=Group(key,policy,listeners,t);groups[caster,identity]=frame;runtime.attack_group_epoch=epoch
    return frame

def interested(manager):return bool(state(manager).resources.get('attack_groups'))

def collect(manager,packet,t):
    frame=state(manager).resources.get('attack_groups',{}).get((packet.attacker,packet.attack_id))
    if frame is None or packet.target.kind not in frame.kinds or packet.outcome==HitOutcome.MISS or packet.credit<=0:return
    if checked_time(t)<frame.opened:raise ValueError('Impact precedes its attack group')
    if packet.target not in frame.targets:
        if len(frame.targets)>=MAX_TARGETS:raise ValueError('Attack target capacity exceeded')
        frame.targets[packet.target]=None

def cancel(manager,frame):
    groups=pool(manager,'attack_groups');key=(frame.key.caster,frame.key.identity)
    if groups.get(key) is frame:groups.pop(key)
    frame.closed=True

def seal(manager,frame,t):
    groups=pool(manager,'attack_groups');key=(frame.key.caster,frame.key.identity)
    if frame.closed or groups.get(key) is not frame:raise ValueError('Attack group is stale or already closed')
    if checked_time(t)<frame.opened:raise ValueError('Attack group closes before it opens')
    result=AttackTargets(frame.key,tuple(frame.targets))
    # A child may reuse the same public attack identity. Parent cleanup must
    # never remove that new epoch, including when a child raises an exception.
    groups.pop(key);frame.closed=True
    sealed=SealedGroup(result,frame.listeners,t)
    pool(manager,'sealed_attack_groups')[result.key]=sealed
    return sealed

def dispatch(manager,sealed,t):
    pending=pool(manager,'sealed_attack_groups');key=sealed.result.key
    if pending.get(key) is not sealed:raise ValueError('Attack group is stale or already dispatched')
    if checked_time(t)<sealed.sealed:raise ValueError('Attack group dispatch precedes its seal')
    pending.pop(key);running=pool(manager,'dispatching_attack_groups');running[key]=sealed
    try:
        for event,threshold in sealed.listeners:
            if len(sealed.result.targets)>=threshold:manager.notify(event,t,key.caster,attack_targets=sealed.result)
        return sealed.result
    finally:
        if running.get(key) is sealed:running.pop(key)

def finish(manager,frame,t):return dispatch(manager,seal(manager,frame,t),t)

@contextmanager
def scope(manager,caster,identity,t,*,kinds):
    frame=begin(manager,caster,identity,t,kinds=kinds)
    try:yield frame
    except BaseException:
        cancel(manager,frame);raise
    else:finish(manager,frame,t)

def install():
    if 'attack_groups' in CATALOG.handlers:return
    from calculator.buff_manager import BuffManager
    BuffManager.begin_attack_targets=begin;BuffManager.finish_attack_targets=finish;BuffManager.cancel_attack_targets=cancel
    original=BuffManager.reset
    @wraps(original)
    def reset(self,*args,**kwargs):
        result=original(self,*args,**kwargs)
        for frame in pool(self,'attack_groups').values():frame.closed=True
        pool(self,'attack_groups').clear()
        pool(self,'sealed_attack_groups').clear();pool(self,'dispatching_attack_groups').clear()
        state(self).attack_group_plans=None
        return result
    BuffManager.reset=reset
    CATALOG.register('attack_groups',Handler(impact=collect,impact_interest=interested))
