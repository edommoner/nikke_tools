"""Explicit typed storage contract for future projectile/shield world adapters.

Quantities arrive already resolved by the caller. This module does not invent
attack selection, projectile movement, shield interception, modifiers or notices.
"""
from dataclasses import dataclass
import math
from impact_specs import ActorHandle,ActorKind,Impact

CAPACITY=128
KINDS=frozenset((ActorKind.PROJECTILE,ActorKind.HP_SHIELD,ActorKind.HIT_SHIELD))

@dataclass
class TargetState:
    handle:ActorHandle
    owner:ActorHandle|None
    capacity:float
    remaining:float
    expires:float
    alive:bool=True

def quantity(x):
    if type(x) not in (int,float) or not math.isfinite(x) or x<0 or x>1e30:raise ValueError('Invalid resolved target quantity')
    return float(x)

class DestructibleTargets:
    def __init__(self,capacity=CAPACITY):
        if type(capacity) is not int or not 1<=capacity<=CAPACITY:raise ValueError('Invalid destructible target capacity')
        self.capacity=capacity;self.rows=[None]*capacity;self.time=0.
    def advance(self,t):
        if type(t) not in (int,float) or not math.isfinite(t) or t<self.time:raise ValueError('Target clocks must be finite and monotonic')
        self.time=float(t)
        for r in self.rows:
            if r is not None and r.alive and r.expires>=0 and t>=r.expires:r.alive=False
    def spawn(self,slot,handle,capacity,expires=-1.,owner=None):
        if type(slot) is not int or not 0<=slot<self.capacity or not isinstance(handle,ActorHandle) or handle.kind not in KINDS:raise ValueError('Invalid destructible binding')
        value=quantity(capacity)
        if value==0 or handle.kind==ActorKind.HIT_SHIELD and (value!=int(value) or value>2**31-1):raise ValueError('Invalid target capacity quantity')
        if type(expires) not in (int,float) or not math.isfinite(expires) or expires!=-1 and expires<=self.time:raise ValueError('Invalid target expiry')
        if owner is not None and (not isinstance(owner,ActorHandle) or owner.kind not in (ActorKind.BODY,ActorKind.ADD)):raise ValueError('Explicit logical shield/projectile owner required')
        old=self.rows[slot]
        if old is not None and (old.alive or old.handle.kind!=handle.kind or old.handle.identity!=handle.identity):raise ValueError('Target slot identity is immutable')
        generation=1 if old is None else old.handle.generation+1
        if handle.generation!=generation:raise ValueError('Spawn generation must advance once')
        if any(i!=slot and r is not None and (r.handle.kind,r.handle.identity)==(handle.kind,handle.identity) for i,r in enumerate(self.rows)):raise ValueError('Duplicate configured target identity')
        self.rows[slot]=TargetState(handle,owner,value,value,float(expires))
    def bind_registry(self,slot,label,registry):
        """Expose live generation and ownership through the existing registry."""
        if type(slot) is not int or not 0<=slot<self.capacity or self.rows[slot] is None:raise ValueError('Bind a configured spawned target')
        initial=self.rows[slot].handle
        def provider():
            current=self.rows[slot]
            return current.handle.generation,current.alive,current.owner
        registry.bind(initial.kind,label,provider,identity=initial.identity)
    def hit(self,slot,impact):
        if type(slot) is not int or not 0<=slot<self.capacity or not isinstance(impact,Impact):raise ValueError('Invalid target receipt')
        quantity(impact.damage);quantity(impact.credit)
        row=self.rows[slot]
        if row is None or row.handle!=impact.target or not row.alive:return dict(delivered=False,broken=False,took=0.)
        available=impact.credit if row.handle.kind==ActorKind.HIT_SHIELD else impact.damage
        took=min(available,row.remaining)
        row.remaining=row.remaining-took
        broken=row.remaining==0.
        if broken:row.alive=False
        return dict(delivered=True,broken=broken,took=took)
    def retire(self,slot,handle):
        if type(slot) is not int or not 0<=slot<self.capacity or not isinstance(handle,ActorHandle):raise ValueError('Invalid target retirement')
        r=self.rows[slot]
        matched=r is not None and r.alive and r.handle==handle
        if matched:r.alive=False
        return bool(matched)
    def select(self,kinds):
        mask=frozenset(kinds)
        if not mask or not mask<=KINDS:raise ValueError('Explicit destructible kind selection required')
        return tuple(i for i,r in enumerate(self.rows) if r is not None and r.alive and r.handle.kind in mask)
