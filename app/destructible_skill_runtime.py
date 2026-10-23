"""Ordinary native scalar damage -> the live typed projectile producer.

The caller supplies an explicit shared scalar context. This is a declared-model
extension, not a claim about missing in-game projectile defense/interception.
"""
from destructible_skill_specs import coefficient
from destructible_attack_runtime import projectiles
import math

def resolve(manager,effect,character,*,base_attack,weapon,defense,when,full_burst=False):
    from calculator.damage import calc_damage,default_hit_type
    if character.get('name') not in manager.squad_names or type(full_burst) is not bool or any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in (base_attack,defense,when)):
        raise ValueError('Explicit finite projectile scalar context required')
    value=coefficient(effect,character)
    if not value:return dict(coefficient=value,damage=0.,crit_frac=0.)
    buffs=manager.get_buffs(character['name'],'__enemy__',when)
    result=calc_damage(base_attack,buffs,weapon,default_hit_type(is_normal_atk=False,is_full_burst=full_burst,coeff=value),enemy_def=defense,expected=True)
    return dict(coefficient=value,damage=float(result['damage']),crit_frac=result['crit_frac'])

def execute(world,manager,effect,character,*,base_attack,weapon,defense,attack_id,full_burst=False):
    if world.last is None or world.finished:raise ValueError('Projectile skill requires an active world frame')
    if type(attack_id) is not int or not 0<=attack_id<2**24:raise ValueError('Invalid projectile attack identity')
    sampled=resolve(manager,effect,character,base_attack=base_attack,weapon=weapon,defense=defense,when=world.last,full_burst=full_burst)
    # Match the ordinary skill's zero-coefficient return before hit arithmetic.
    receipts=() if not sampled['coefficient'] else projectiles(world,manager,character['name'],1,2,sampled['damage'],1.,attack_id)
    return sampled,receipts
