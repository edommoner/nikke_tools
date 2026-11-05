"""Scoped native damage callback using the ordinary manager's notify/budget loop.

The enclosing battle owns time, scalar context, and full-burst state. This hook
replaces no global handler and restores the previous manager callback on exit.
"""
from contextlib import contextmanager
from destructible_skill_runtime import execute
from impact_specs import ActorKind

@contextmanager
def projectile_handler(manager,world,character,*,base_attack,weapon,defense,attack_id,observe):
    previous=manager._damage_handler
    original_resolver=manager._resolve_target
    sentinel=object();previous_instance_resolver=manager.__dict__.get('_resolve_target',sentinel)
    def resolve_target(target,caster,*args,**kwargs):
        if target=='all_projectiles':return [world.bindings[i].label for i in world.targets.select([ActorKind.PROJECTILE])]
        return original_resolver(target,caster,*args,**kwargs)
    def handler(effect,caster,t):
        if effect.get('target')!='all_projectiles':
            if previous is None:raise ValueError('No handler for non-projectile damage')
            return previous(effect,caster,t)
        if caster!=character['name'] or world.last!=t:raise ValueError('Projectile callback owner/frame mismatch')
        sampled,receipts=execute(world,manager,effect,character,base_attack=base_attack,weapon=weapon,defense=defense,attack_id=attack_id,full_burst=bool(manager.state.get('full_burst',False)))
        observe(effect,sampled,receipts)
        if receipts and sampled['coefficient'] and effect.get('name'):
            from calculator.timeline import _notify_frac
            fired=[]
            _notify_frac(manager,'skill_crit:'+effect['name'],caster,sampled['crit_frac'],lambda:fired.append(1))
            manager.notify('hit_count:'+effect['name'],t,caster,hit_crit=bool(fired))
    manager.register_damage_handler(handler)
    manager._resolve_target=resolve_target
    try:yield
    finally:
        manager._damage_handler=previous
        if previous_instance_resolver is sentinel:manager.__dict__.pop('_resolve_target',None)
        else:manager._resolve_target=previous_instance_resolver
