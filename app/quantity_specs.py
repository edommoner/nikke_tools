"""Quantity sources are independent of character identity and damage multipliers."""
MAX_AMMO_SCALE=-4
FIXED_PARENT_DAMAGE=36

def validate_quantity(effect):
    """Reject mixed interpretations before compiling the shared operations."""
    ammo=effect.get('scaling')=='max_ammo_count'
    fixed=effect.get('stat')=='dealt_fixed_damage'
    if ammo and (effect.get('type')!='buff' or effect.get('scaling_ref')):
        raise ValueError('Final-ammunition scaling requires a numeric recipient buff without a named reference')
    if fixed:
        if effect.get('type')!='damage' or effect.get('scaling') or any(k in effect for k in ('tick_interval','damage_formula','hit_count_gauge_ref','attack_landing','ramp_interval','ramp_damage_stack','post_ramp_tick_delay','hits_parts')):
            raise ValueError('Parent-damage percentage cannot be combined with coefficient/periodic/part scaling')
        if effect.get('target') not in ('target','target_body','boss','enemy','all_enemies'):
            raise ValueError('Parent fixed damage requires an enemy-body target')
    return ammo,fixed
