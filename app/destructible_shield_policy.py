"""Declared shield interception, not inferred from allied shield rules.

V1: explicit canonical boss handle; first live matching HP shield by binding
slot. V2 explicitly opts into the same slot order across HP and hit shields.
One packet is absorbed without overflow or retargeting; hit shields consume
packet credit. Physical weapons, adds and piercing need their own policy.
"""
from impact_specs import ActorHandle,ActorKind

BOSS=ActorHandle(ActorKind.BODY,0,1)

def validate_owner(owner):
    if not isinstance(owner,ActorHandle) or owner!=BOSS:
        raise ValueError('Shield interception requires the explicit canonical boss handle')

def select(world,owner,*,hit_shields=False):
    validate_owner(owner)
    if type(hit_shields) is not bool:raise ValueError('Explicit hit-shield policy boolean required')
    if world.last is None or world.finished:raise ValueError('Shield selection requires an active battle frame')
    kinds=[ActorKind.HP_SHIELD,ActorKind.HIT_SHIELD] if hit_shields else [ActorKind.HP_SHIELD]
    for slot in world.targets.select(kinds):
        row=world.targets.rows[slot]
        if row.owner==owner:return (slot,row.handle)
    return None
