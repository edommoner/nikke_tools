"""Explicit reference contract for distinct generation-scoped lock membership.

Ranking belongs to a separately declared geometry provider. This module never
turns named carrier stacks into targets, guesses a distance metric, or aliases
parts/projectiles/shields to the body. No public battle admission is added.
"""
from dataclasses import dataclass
from impact_specs import ActorHandle,ActorKind,enum_value
from world_actor_runtime import ActorSnapshot,ActorRegistry
from effect_target_count_policy import query,MODEL as CAPACITY_MODEL

MODEL='named-generation-locks-v1'
MAX_ACTORS=256
MAX_REVISION=2147483647


@dataclass(frozen=True)
class RemovedLock:
    handle:ActorHandle
    reason:str


@dataclass(frozen=True)
class LockSnapshot:
    revision:int
    handles:tuple[ActorHandle,...]


@dataclass(frozen=True)
class Acquisition:
    selected:ActorHandle|None
    reason:str
    removed:tuple[RemovedLock,...]
    snapshot:LockSnapshot


def _key(handle):return (handle.kind,handle.identity)


class GenerationLocks:
    """Insertion-ordered distinct membership; actor/capacity changes are explicit.

    Candidate order is supplied externally; no distance or ranking is computed.
    A lower capacity blocks new acquisitions without evicting existing locks.
    Physical clear timing and delivery/retargeting order belong to the caller.
    Snapshots remain immutable when live membership subsequently changes.
    """
    def __init__(self,*,capacity_limit,eligible_kinds,model):
        if model!=MODEL or type(capacity_limit) is not int or not 1<=capacity_limit<=MAX_ACTORS:
            raise ValueError('Explicit bounded lock model required')
        kinds=tuple(enum_value(ActorKind,k) for k in eligible_kinds)
        if not kinds or len(kinds)!=len(set(kinds)):raise ValueError('Explicit unique actor kinds required')
        self.capacity_limit=capacity_limit;self.eligible=frozenset(kinds)
        self._handles=();self._generations={};self._revision=0

    def snapshot(self):return LockSnapshot(self._revision,self._handles)

    def _prepared(self,views):
        rows=tuple(views)
        if len(rows)>MAX_ACTORS:raise ValueError('Lock actor view capacity exceeded')
        current={};generations=dict(self._generations)
        for row in rows:
            if not isinstance(row,ActorSnapshot):raise ValueError('Typed live actor snapshots required')
            key=_key(row.handle)
            if key in current:raise ValueError('Duplicate configured actor identity')
            if row.handle.generation<generations.get(key,0):raise ValueError('Actor generation moved backwards')
            current[key]=row;generations[key]=row.handle.generation
        if len(generations)>MAX_ACTORS:raise ValueError('Lock generation history capacity exceeded')
        kept=[];removed=[]
        for handle in self._handles:
            row=current.get(_key(handle))
            if row is None or not row.alive:removed.append(RemovedLock(handle,'not_live'))
            elif row.handle!=handle:removed.append(RemovedLock(handle,'generation_replaced'))
            else:kept.append(handle)
        return current,generations,tuple(kept),tuple(removed)

    def _commit(self,generations,handles,*,action):
        revision=self._revision+int(action)
        if revision>MAX_REVISION:raise ValueError('Lock revision exhausted')
        self._generations=generations;self._handles=handles;self._revision=revision

    def sync(self,views):
        _,generations,kept,removed=self._prepared(views)
        self._commit(generations,kept,action=bool(removed));return removed

    def acquire(self,views,candidates,*,capacity):
        if type(capacity) is not int or not 0<=capacity<=self.capacity_limit:
            raise ValueError('Lock capacity outside the declared exact bound')
        choices=tuple(candidates)
        if len(choices)>MAX_ACTORS or any(not isinstance(c,ActorHandle) for c in choices):
            raise ValueError('Typed bounded lock candidates required')
        if len(set(choices))!=len(choices):raise ValueError('Duplicate logical lock candidate')
        current,generations,kept,removed=self._prepared(views)
        selected=None;reason='capacity_reached' if len(kept)>=capacity else 'no_live_unlocked_candidate'
        if len(kept)<capacity:
            for candidate in choices:
                row=current.get(_key(candidate))
                if (candidate.kind not in self.eligible or candidate in kept
                    or row is None or not row.alive or row.handle!=candidate):continue
                selected=candidate;reason='acquired';kept=(*kept,selected);break
        self._commit(generations,kept,action=bool(removed) or selected is not None)
        return Acquisition(selected,reason,removed,self.snapshot())

    def clear(self,reason):
        if reason not in ('normal_attack','taking_cover'):raise ValueError('Explicit lock clear event required')
        before=self.snapshot();self._commit(dict(self._generations),(),action=True);return before


def registry_views(registry):
    """Use real current providers; missing pre-birth actors have no live handle."""
    if not isinstance(registry,ActorRegistry):raise ValueError('Existing typed actor registry required')
    if len(registry.identities)>MAX_ACTORS:raise ValueError('Lock actor registry capacity exceeded')
    rows=[]
    for (kind,identity),label in sorted(registry.identities.items()):
        bound,provider=registry.bindings[kind,label]
        if bound!=identity:raise ValueError('Actor registry identity mapping changed')
        generation,alive,parent=provider()
        if type(generation) is int and generation==0:
            if alive is not False or parent is not None and not isinstance(parent,ActorHandle):
                raise ValueError('Malformed pre-birth actor provider')
            continue
        rows.append(ActorSnapshot(ActorHandle(kind,identity,generation),label,alive,parent))
    return tuple(rows)


@dataclass(frozen=True)
class NamedSnapshot:
    caster:str
    marker:str
    time:float
    capacity:int
    state:LockSnapshot


class NamedGenerationLocks:
    """Read the existing quota fresh on each acquisition/snapshot, never cache it."""
    def __init__(self,manager,caster,marker,*,base_count,capacity_limit,eligible_kinds,model):
        from calculator.buff_manager import BuffManager
        if (not isinstance(manager,BuffManager) or caster not in manager.squad_names or not isinstance(marker,str) or not marker
            or type(base_count) is not int or type(capacity_limit) is not int or not 0<=base_count<=capacity_limit):
            raise ValueError('Explicit named lock caster/marker/base required')
        self.core=GenerationLocks(capacity_limit=capacity_limit,eligible_kinds=eligible_kinds,model=model)
        self.manager=manager;self.caster=caster;self.marker=marker;self.base_count=base_count

    def capacity(self,when):
        return query(self.manager,self.caster,self.marker,when,base_count=self.base_count,
            capacity_limit=self.core.capacity_limit,model=CAPACITY_MODEL)['capacity']

    def acquire(self,registry,candidate_provider,when):
        capacity=self.capacity(when);views=registry_views(registry)
        if not callable(candidate_provider):raise ValueError('Explicit ordered candidate provider required')
        eligible=tuple(row for row in views if row.alive and row.handle.kind in self.core.eligible)
        choices=candidate_provider(eligible)
        return self.core.acquire(views,choices,capacity=capacity)

    def capture(self,registry,when):
        capacity=self.capacity(when);self.core.sync(registry_views(registry))
        return NamedSnapshot(self.caster,self.marker,float(when),capacity,self.core.snapshot())

    def clear(self,reason):return self.core.clear(reason)
