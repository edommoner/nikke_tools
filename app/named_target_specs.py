"""Immutable named-attack references; never character-specific execution rules.

The detailed world currently has one aimed enemy. Target identity therefore
aliases that enemy, but repetition is separate from coefficient stack scaling.
DoT ramps need their own scheduled lifecycle and are deliberately not admitted
by this immediate/deferred bonus-damage contract.
"""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class NamedAttackTarget:
    reference: str
    deferred_bonus_hits: int

def resolve_named_attack(effect,caster,effects):
    target=effect.get('target')
    if not isinstance(target,str) or not target.startswith('same_target:'):return None
    reference=target[len('same_target:'):]
    if not reference:raise ValueError('named attack target requires a nonempty reference')
    if effect.get('type')!='damage' or effect.get('stat')!='bonus_damage' or effect.get('tick_interval'):
        raise ValueError('named attack target requires bonus damage; periodic ramps remain unsupported')
    matches=[other for other,owner in effects if owner==caster and other.get('name')==reference]
    if len(matches)!=1:raise ValueError('named attack target reference must resolve exactly once for its caster')
    attack=matches[0];stat=attack.get('stat','');parts=stat.split(':')
    if attack.get('type')!='damage' or parts[0] not in ('damage','burst_damage','armor_break_damage','armor_break_burst_damage','sequential_damage','split_damage','bonus_damage'):
        raise ValueError('named attack target must reference a direct damage definition')
    enemy=attack.get('target','')
    if not isinstance(enemy,str) or not (enemy in ('enemy','target','target_body','same_target','boss','all_enemies') or enemy.startswith('enemies_')):
        raise ValueError('named attack target reference must select the single aimed enemy')
    if len(parts)>2 or len(parts)==2 and not re.fullmatch(r'[1-9][0-9]*',parts[1]):
        raise ValueError('named attack target currently requires a positive literal attack count')
    count=int(parts[1]) if len(parts)==2 else 1
    if count>4096:raise ValueError('named attack target count exceeds execution capacity')
    return NamedAttackTarget(reference,count)
