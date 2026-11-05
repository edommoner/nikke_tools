"""Produce one resolved attack over the currently live projectile set.

Selection is frozen before synchronous children. Damage has already been
resolved; this adapter supplies no shield interception or damage-factor rules.
"""
from destructible_impact_runtime import deliver
from impact_specs import ActorHandle,ActorKind,Impact

def projectiles(world,manager,attacker,family,outcome,damage,credit=1.,attack_id=0):
    # Validate even an empty selection, before publishing anything.
    Impact(attacker,ActorHandle(ActorKind.PROJECTILE,0),family,outcome,damage,credit,attack_id)
    if attacker not in manager.squad_names or world.last is None or world.finished:
        raise ValueError('Projectile attack requires an active frame and allied attacker')
    when=world.last
    selected=tuple((slot,world.targets.rows[slot].handle) for slot in world.targets.select([ActorKind.PROJECTILE]))
    packets=tuple((slot,Impact(attacker,handle,family,outcome,damage,credit,attack_id)) for slot,handle in selected)
    answers=[]
    for slot,packet in packets:
        if world.last!=when or world.finished:raise ValueError('Projectile attack frame changed during synchronous children')
        answers.append((slot,packet.target,deliver(world,manager,slot,packet)))
    return tuple(answers)
