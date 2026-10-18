"""Stable configured identities with live spawn generations, separate from damage.

Relationships describe ownership only. They do not decide which colliders count
as distinct enemies or how a skill chooses its recipients.
"""
from dataclasses import dataclass
from effect_runtime import state
from impact_specs import ActorHandle,ActorKind,enum_value
from world_actor_specs import bindings,BODY_SOURCE,PART_SOURCE,ADD_SOURCE

@dataclass(frozen=True)
class ActorSnapshot:
    handle:ActorHandle
    label:str
    alive:bool
    parent:ActorHandle|None=None
    def __post_init__(self):
        if not isinstance(self.handle,ActorHandle) or not isinstance(self.label,str) or not self.label or type(self.alive) is not bool or self.parent is not None and not isinstance(self.parent,ActorHandle):
            raise ValueError('Invalid world actor snapshot')

class ActorRegistry:
    def __init__(self):self.bindings={};self.identities={};self.next_identity={}
    def bind(self,kind,label,provider,identity=None):
        kind=enum_value(ActorKind,kind)
        if not isinstance(label,str) or not label or not callable(provider):raise ValueError('Invalid world actor binding')
        identity=self.next_identity.get(kind,0) if identity is None else identity
        ActorHandle(kind,identity)
        if (kind,label) in self.bindings or (kind,identity) in self.identities:raise ValueError('World actor identity is already bound')
        self.bindings[kind,label]=(identity,provider);self.identities[kind,identity]=label;self.next_identity[kind]=max(self.next_identity.get(kind,0),identity+1)
    def view(self,kind,label):
        kind=enum_value(ActorKind,kind)
        try:identity,provider=self.bindings[kind,label]
        except KeyError:raise ValueError('Unknown world actor (explicit handle required): '+str(label)) from None
        generation,alive,parent=provider()
        if type(generation) is not int or generation<1:raise ValueError('World actor has not spawned: '+label)
        return ActorSnapshot(ActorHandle(kind,identity,generation),label,alive,parent)
    def identity(self,kind,label):
        try:return self.bindings[enum_value(ActorKind,kind),label][0]
        except KeyError:raise ValueError('Unknown world actor (explicit handle required): '+str(label)) from None
    def exact(self,handle):
        if not isinstance(handle,ActorHandle):raise TypeError('World actor lookup requires a handle')
        try:label=self.identities[handle.kind,handle.identity]
        except KeyError:raise ValueError('Unknown world actor handle') from None
        result=self.view(handle.kind,label)
        if result.handle!=handle:raise ValueError('Stale world actor generation')
        return result
    def root(self,handle):
        seen=set();result=self.exact(handle)
        while result.parent is not None:
            if result.handle in seen:raise ValueError('Cyclic world actor relationship')
            seen.add(result.handle);result=self.exact(result.parent)
        return result


def set_control_aim(manager,caster,actor):
    if caster not in manager.squad_names or not isinstance(actor,ActorHandle) or actor.kind not in (ActorKind.BODY,ActorKind.PART,ActorKind.ADD):raise ValueError('Invalid actor aim input')
    runtime=state(manager);bound=getattr(runtime,'world_actor_registry',None)
    if bound is None or not bound[1].exact(actor).alive:raise ValueError('Actor aim requires a live configured actor')
    if not hasattr(runtime,'control_aims'):runtime.control_aims={}
    runtime.control_aims[caster]=actor


def sample_control_aim(manager,caster):
    runtime=state(manager);aims=getattr(runtime,'control_aims',None);actor=aims.get(caster) if aims else None
    if actor is None:return None
    bound=getattr(runtime,'world_actor_registry',None)
    if bound is not None:
        try:
            if bound[1].exact(actor).alive:return actor
        except ValueError:pass
    return ActorHandle(ActorKind.BODY,0,1)

def registry_for(manager,boss):
    runtime=state(manager);cached=getattr(runtime,'world_actor_registry',None)
    if cached is not None and cached[0] is boss:return cached[1]
    registry=ActorRegistry()
    runs=boss._runs if boss is not None else []
    for b in bindings([run.p for run in runs]):
        if b.source==BODY_SOURCE:provider=lambda:(1,True,None)
        else:
            run=runs[b.run]
            def provider(run=run,b=b):
                actors=run.targets if b.source==PART_SOURCE else run.adds
                alive=run.active and b.slot<len(actors) and (not actors[b.slot].destroyed if b.source==PART_SOURCE else actors[b.slot].alive)
                return run.opens,bool(alive),b.parent
        registry.bind(b.kind,b.label,provider,identity=b.identity)
    runtime.world_actor_registry=(boss,registry)
    if hasattr(runtime,'control_aims'):runtime.control_aims.clear()
    return registry
