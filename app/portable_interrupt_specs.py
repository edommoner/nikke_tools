"""Private world-pool identity, outside the canonical typed impact namespace.

Canonical ActorKind2 remains PROJECTILE. Interrupts have no typed impact bridge
in the pinned reference; kind6 is a private pool identity, never hit credit.
"""
from dataclasses import dataclass,field
from world_actor_specs import bindings
KIND=6
SOURCE=3
@dataclass(frozen=True)
class InterruptBinding:
    identity:int
    label:str
    run:int
    slot:int
    kind:int=field(default=KIND,init=False)
    source:int=field(default=SOURCE,init=False)
    parent:None=field(default=None,init=False)
def pool_bindings(patterns):
    rows=list(bindings(patterns));identity=0
    for run,p in enumerate(patterns):
        if p.kind!='interrupt':continue
        for slot,target in enumerate(p.targets):
            rows.append(InterruptBinding(identity,target.name,run,slot));identity+=1
    return tuple(rows)
