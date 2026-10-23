"""Typed target receipts into the existing synchronous impact/counter executor.

The caller supplies a resolved Impact. This adapter adds no damage factors,
scoring, selection or enemy_death event. Counter retirement is generation scoped.
"""
from effect_runtime import publish_impact
from target_counter_runtime import target_death
from impact_specs import ActorHandle,Impact
from destructible_target_state import KINDS

def deliver(world,manager,slot,impact):
    if not isinstance(impact,Impact) or impact.target.kind not in KINDS or impact.attacker not in manager.squad_names:
        raise ValueError('Typed landing requires an explicit destructible handle and allied attacker')
    when=world.last
    receipt=world.hit(slot,impact)
    if not receipt['delivered']:return receipt
    # hit() captures the old generation/owner before any synchronous children.
    publish_impact(manager,impact,when)
    if receipt['broken']:
        target_death(manager,ActorHandle(*receipt['notice']['handle']),when)
    return receipt
