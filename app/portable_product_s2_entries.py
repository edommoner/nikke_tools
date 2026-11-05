"""Explicit same-wire wrappers for existing S2 product compositions."""
ORDINARY = {
    'gpu/product_target_battle_entry.slang':'gpu/product_ordinary_lock_target_battle_entry.slang',
    'gpu/product_fixed_target_battle_entry.slang':'gpu/product_ordinary_lock_fixed_target_battle_entry.slang',
    'gpu/product_group_battle_entry.slang':'gpu/product_ordinary_lock_group_battle_entry.slang',
    'gpu/product_fixed_group_battle_entry.slang':'gpu/product_ordinary_lock_fixed_group_battle_entry.slang',
    'gpu/product_group_target_battle_entry.slang':'gpu/product_ordinary_lock_group_target_battle_entry.slang',
    'gpu/product_fixed_group_target_battle_entry.slang':'gpu/product_ordinary_lock_fixed_group_target_battle_entry.slang',
    'gpu/product_healing_battle_entry.slang':'gpu/product_ordinary_lock_healing_battle_entry.slang',
    'gpu/product_healing_fixed_battle_entry.slang':'gpu/product_ordinary_lock_healing_fixed_battle_entry.slang',
    'gpu/product_healing_group_battle_entry.slang':'gpu/product_ordinary_lock_healing_group_battle_entry.slang',
    'gpu/product_healing_fixed_group_battle_entry.slang':'gpu/product_ordinary_lock_healing_fixed_group_battle_entry.slang',
    'gpu/product_ammo_battle_entry.slang':'gpu/product_ordinary_lock_ammo_battle_entry.slang',
    'gpu/product_ammo_fixed_battle_entry.slang':'gpu/product_ordinary_lock_ammo_fixed_battle_entry.slang',
}
BASE_WIRES = {
    'gpu/product_battle_entry.slang':(104400,786432),
    'gpu/product_fixed_battle_entry.slang':(104400,786432),
    'gpu/product_target_battle_entry.slang':(110112, 1048576),
    'gpu/product_fixed_target_battle_entry.slang':(110112, 1048576),
    'gpu/product_group_battle_entry.slang':(104408, 1048576),
    'gpu/product_fixed_group_battle_entry.slang':(104408, 1048576),
    'gpu/product_group_target_battle_entry.slang':(104672, 1048576),
    'gpu/product_fixed_group_target_battle_entry.slang':(104672, 1048576),
    'gpu/product_healing_battle_entry.slang':(120048, 2032000),
    'gpu/product_healing_fixed_battle_entry.slang':(120048, 2032000),
    'gpu/product_healing_group_battle_entry.slang':(120048, 2032000),
    'gpu/product_healing_fixed_group_battle_entry.slang':(120048, 2032000),
}
ALIASES = {value:key for key,value in ORDINARY.items()}
ALIASES.update({
    'gpu/product_named_carriers_target_battle_entry.slang':'gpu/product_target_battle_entry.slang',
    'gpu/product_named_carriers_fixed_target_battle_entry.slang':'gpu/product_fixed_target_battle_entry.slang',
})

def checked_wrapper(source,iw,ow):
    if source in BASE_WIRES:return BASE_WIRES[source]==(iw,ow)
    if source in ('gpu/product_ammo_battle_entry.slang','gpu/product_ammo_fixed_battle_entry.slang'):
        from portable_backend import validate_composed_stride
        validate_composed_stride(source,iw,ow)
        return True
    return False
ALIASES['gpu/product_ordinary_lock_cover_battle_entry.slang']='gpu/product_cover_battle_entry.slang'
ALIASES['gpu/product_ordinary_lock_cover_fixed_battle_entry.slang']='gpu/product_cover_fixed_battle_entry.slang'
