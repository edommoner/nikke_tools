"""Literal parent-percent tag; no parent damage or schedule is CPU supplied."""
from quantity_specs import validate_quantity
FLAG=262144

def enabled(effect):return effect.get('type')=='damage' and effect.get('stat')=='dealt_fixed_damage'
def validate(effect,*,combat,world_frame):
    if not enabled(effect):return False
    validate_quantity(effect)
    if combat is None or not world_frame:raise ValueError('Parent fixed damage requires a private combat world')
    return True
