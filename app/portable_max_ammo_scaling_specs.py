"""Live final-ammunition quantity, distinct from a named-stack reference."""
from quantity_specs import validate_quantity,MAX_AMMO_SCALE
FLAG=4096

def enabled(effect):return effect.get('scaling')=='max_ammo_count'
def validate(effect,*,combat,world_frame):
    if not enabled(effect):return False
    validate_quantity(effect)
    if effect.get('stat')!='charge_dmg_pct':raise ValueError('Final-ammunition scaling requires a supported numeric charge-damage buff')
    if effect.get('tick_interval'):raise ValueError('Periodic final-ammunition scaling is not admitted')
    if combat is None or not world_frame:raise ValueError('Final-ammunition scaling requires a private combat world')
    return True
