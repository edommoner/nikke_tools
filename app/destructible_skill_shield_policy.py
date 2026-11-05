"""Explicit one-boss skill interception without changing authored selectors.

The ordinary handler retains target spelling, family flags, coefficient, named
hit notices and gauge. This policy currently excludes deferred/multi-hit skills.
"""
from destructible_skill_specs import coefficient
from portable_enemy_specs import damage_plan

def skill(effect,character,*,allow_split=False):
    if type(allow_split) is not bool:raise ValueError('Explicit split policy boolean required')
    if effect.get('stat') not in (('damage','burst_damage','split_damage') if allow_split else ('damage','burst_damage')):raise ValueError('Declared shield skill supports plain or burst damage only')
    route,count,hits=damage_plan(effect)
    if route not in range(1,10) or not 1<=count<=128 or hits!=1:raise ValueError('Declared shield skill requires a direct single-boss selector')
    value_effect=dict(effect,stat='damage',target='all_projectiles')
    if allow_split:value_effect.pop('note',None)
    value=coefficient(value_effect,character)
    return dict(route=route,count=count,coefficient=value)

def accumulation_skill(effect):
    from portable_damage_accum_specs import validate
    if effect.get('stat')!='accum_split_damage' or not validate(effect,combat=True,world_frame=True):raise ValueError('Accumulated quantity definition required')
    allowed={'source','type','name','trigger','target','stat','target_effect','max_trigger','note'}
    if set(effect)-allowed:raise ValueError('Unsupported accumulated quantity field')
    route,count,hits=damage_plan(effect)
    if route not in range(1,10) or hits!=1 or not 1<=count<=128:raise ValueError('Accumulated shield quantity requires a direct single-boss selector')
    trigger=effect.get('trigger',{})
    if set(trigger)-{'timing','condition'} or trigger.get('condition',[]):raise ValueError('Unsupported accumulated quantity trigger')
    return dict(route=route,count=count,coefficient=0.)
