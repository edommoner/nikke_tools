"""Narrow native-equivalent metadata, never an effect-local weapon override.

The current native auto_damage handler reads actor weapons, not this annotation.
Only matching base-weapon declarations are admitted. Contradictions remain a
reference-model question, even though the current CPU ignores them too.
"""
from portable_geometry_specs import WEAPONS

def declaration(effect):
    if 'weapon_type' not in effect or effect.get('type')=='weapon_change':return None
    if effect.get('type')!='damage' or effect.get('stat')!='auto_damage' or effect.get('damage_formula')!='normal_attack':return None
    value=effect['weapon_type']
    if not isinstance(value,str) or value not in WEAPONS:raise ValueError('Skill weapon annotation requires a known weapon type')
    return value

def validate_binding(effect,metadata):
    value=declaration(effect)
    if value is not None and value!=metadata.get('weapon_type'):raise ValueError('Skill weapon annotation differs from native caster base weapon; override semantics unresolved')
    return value
