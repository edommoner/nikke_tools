"""Explicit one-boss skill interception without changing authored selectors.

The ordinary handler retains target spelling, family flags, coefficient, named
hit notices and gauge. This policy currently excludes deferred/multi-hit skills.
"""
from destructible_skill_specs import coefficient
from portable_enemy_specs import damage_plan

def skill(effect,character):
    if effect.get('stat') not in ('damage','burst_damage'):raise ValueError('Declared shield skill supports plain or burst damage only')
    route,count,hits=damage_plan(effect)
    if route not in range(1,10) or not 1<=count<=128 or hits!=1:raise ValueError('Declared shield skill requires a direct single-boss selector')
    value=coefficient(dict(effect,stat='damage',target='all_projectiles'),character)
    return dict(route=route,count=count,coefficient=value)
