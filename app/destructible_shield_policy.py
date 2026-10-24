"""Declared HP-shield interception, not inferred from allied shield rules.

V1: explicit canonical boss handle; first live matching HP shield by binding
slot. One packet is absorbed without overflow or retargeting. Physical weapons,
hit shields, adds and piercing require their own producer policy.
"""
from impact_specs import ActorHandle,ActorKind

BOSS=ActorHandle(ActorKind.BODY,0,1)

def validate_owner(owner):
    if not isinstance(owner,ActorHandle) or owner!=BOSS:
        raise ValueError('Shield interception requires the explicit canonical boss handle')

def select(world,owner):
    validate_owner(owner)
    if world.last is None or world.finished:raise ValueError('Shield selection requires an active battle frame')
    for slot in world.targets.select([ActorKind.HP_SHIELD]):
        row=world.targets.rows[slot]
        if row.owner==owner:return (slot,row.handle)
    return None
