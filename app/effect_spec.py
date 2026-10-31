"""Shared effect taxonomy and stable numerical ABI. No battle results live here.

Classification describes semantics; it never grants compiler support. Parsed
variants must still pass the strict compiler. CPU parity is regression evidence,
not authority over documented in-game behavior.
"""
from importlib import import_module

# Ordered semantic stages; the existing reference implementation uses wrappers.
# A later executor rewrite must preserve these dependencies and event order.
COMPAT_LAYERS = (
    'target_context_runtime', 'survival_compat', 'survival_scaling_compat', 'outgoing_healing_compat',
    'healing_storage_compat', 'heal_sharing_compat', 'heal_charge_compat', 'damage_accum_runtime',
    'max_hp_snapshot_runtime',
    'base_copy_runtime',
    'damage_query_runtime',
    'weapon_mode_runtime',
    'world_frame_runtime',
    'impact_runtime',
    'attack_group_runtime',
    'target_counter_runtime',
    'periodic_source_runtime',
    'staged_dot_runtime',
    'enemy_recipient_runtime',
    'periodic_target_runtime',
    'boss_dot_clock_compat',
)

def install_reference_layers():
    for module in COMPAT_LAYERS:
        import_module(module).install()

# Different quantities share lifecycle conventions, not their numerical rules.
RECOVERY_ORDER = ('source_and_recipient_modifiers', 'sharing_allocation',
                  'received_healing_accumulation', 'body_hp_clamp', 'overheal_storage',
                  'hp_edge_events', 'original_target_notification')

FAMILIES = {
    'damage': 'damage split_damage bonus_damage burst_damage sequential_damage projectile_attachment_damage projectile_explosion_damage dot_damage armor_break_damage armor_break_burst_damage core_damage accum_split_damage dealt_fixed_damage auto_damage',
    'damage_modifiers': 'atk_pct atk_flat atk_caster_based_pct atk_from_hp_pct atk_copy def_pct def_caster_based_pct enemy_def_down_pct enemy_def_down_flat def_ignore_pct crit_rate crit_dmg core_dmg_pct atk_dmg_pct normal_atk_dmg_pct received_dmg_pct split_dmg_pct sequential_dmg_pct projectile_attachment_dmg_pct projectile_explosion_dmg_pct projectile_dmg_pct element_bonus element_bonus_pct intercept_dmg_pct part_dmg_pct armor_break_dmg_pct shield_dmg_pct dot_dmg_pct burst_dmg_pct burst_dmg_aoe_pct burst_dmg_single_pct normal_atk_crit_rate normal_atk_crit_dmg crit_rate_skill crit_dmg_skill dmg_scale_mag_pct atk_buff_mag_pct received_dmg_buff_mag_pct damage_reduction_pct',
    'weapon': 'accuracy_pct pierce_enabled pierce_dmg_pct armor_break_enabled pierce_range explosion_range effect_range_pct pellet_count pellet_count_fixed attack_speed_pct mg_warmup_speed_pct element_code_override lock_on focus_fire weapon_change optimal_range_min optimal_range_max_pct',
    'charge': 'charge_dmg_pct charge_dmg_mag_pct charge_speed_pct charge_time_flat charge_time_fixed charge_speed_caster_based_pct burst_charge_speed_pct charge_speed_overflow_conversion_pct charge_speed_buff_immune charge_speed_debuff_immune',
    'ammo_reload': 'max_ammo_pct max_ammo_flat ammo_charge_pct ammo_charge_flat reload_speed_pct reload_ratio_pct reload_time_fixed force_reload infinite_ammo gauge_consume_as_ammo squad_ammo_consume_as',
    'burst_cooldown': 'burst_cooldown burst_cooldown_reduce burst_charge_pct burst_stage_override burst_reentry fullburst_duration skill_cooldown skill_cooldown_pct skill_cooldown_reduce_pct force_skill_use',
    'resource_accumulation': 'gauge_charge gauge_consume gauge_max_add gauge_charge_enabled dmg_accum_rate_pct dmg_accum_dealt_atk_pct dmg_accum_received_atk_pct target_hit_counter',
    'hp': 'max_hp_pct max_hp_only_pct hp_caster_based_pct hp_only_caster_based_pct max_hp_from_max_hp_pct hp_copy current_hp_reduce revive',
    'healing': 'heal_hp_pct heal_received_pct outgoing_heal_pct lifesteal_pct',
    'healing_buffers': 'heal_overcharge_store heal_overcharge_store_atk_pct accumulate_max_scale_pct heal_overcharge_discharge heal_split',
    'protection': 'shield_from_max_hp_pct shared_shield_from_max_hp_pct next_shield_hp_pct shield_heal_pct shield_invincible cover_def_pct cover_hp_pct cover_disabled cover_heal_pct cover_revive decoy decoy_heal_pct received_dmg_split received_dmg_split_even',
    'control_survival': 'stun stun_immune stealth taunt invincible undying force_move enemy_movement_disable possessed',
    'effect_lifecycle': 'remove_named_buff named_buff_duration_extend buff_stack_add buff_stack_remove buff_stack_init buff_max_stack_add debuff_stack_add debuff_stack_remove debuff_immune debuff_immune_count debuff_cleanse enemy_buff_cleanse trigger_count_reduce effect_interval effect_target_count_add stack_change_immune',
    'character_state': 'periodic_source_refresh feather_refresh persona_state',
}
_FAMILY_BY_STAT = {stat:family for family,stats in FAMILIES.items() for stat in stats.split()}
assert sum(len(s.split()) for s in FAMILIES.values()) == len(_FAMILY_BY_STAT), 'Duplicate taxonomy entry'

MODEL_CHOICES = frozenset(('heal_overcharge_store', 'heal_split',
    'heal_overcharge_store_atk_pct', 'accumulate_max_scale_pct', 'heal_overcharge_discharge',
    'outgoing_heal_pct','dmg_accum_dealt_atk_pct','dmg_accum_received_atk_pct',
    'dmg_accum_rate_pct','accum_split_damage','max_hp_from_max_hp_pct','atk_copy','hp_copy'))

def describe_effect(effect):
    """Classify a definition without assuming its entire form is implemented."""
    stat=effect.get('stat')
    root=stat.split(':',1)[0] if isinstance(stat,str) else None
    family=('weapon' if effect.get('type')=='weapon_change' else
            'effect_lifecycle' if root is None else _FAMILY_BY_STAT.get(root,'unclassified'))
    return {'family':family,'stat_root':root,
            'evidence':'explicit_reference_model' if root in MODEL_CHOICES else 'requires_mechanic_evidence',
            'registered_numeric_stat':stat in DETAIL_STAT or stat in EXTRA_STAT,
            'scoped_inert':stat in SCOPED_INERT,
            'compiler_acceptance_required':True}
COARSE_STAT = {'atk_pct': 0,
 'atk_flat': 1,
 'enemy_def_down_pct': 2,
 'enemy_def_down_flat': 3,
 'def_ignore_pct': 4,
 'crit_rate': 5,
 'crit_dmg': 6,
 'core_dmg_pct': 7,
 'charge_dmg_pct': 8,
 'charge_dmg_mag_pct': 9,
 'atk_dmg_pct': 10,
 'normal_atk_dmg_pct': 11,
 'received_dmg_pct': 12,
 'burst_dmg_pct': 13,
 'sequential_dmg_pct': 14,
 'projectile_attachment_dmg_pct': 15,
 'projectile_explosion_dmg_pct': 16,
 'element_bonus': 17,
 'max_ammo_pct': 18,
 'reload_speed_pct': 19,
 'charge_speed_pct': 20,
 'accuracy_pct': 21,
 'normal_atk_crit_rate': 22,
 'normal_atk_crit_dmg': 23}

DETAIL_STAT = {**COARSE_STAT, **{'crit_rate_skill': 24,
 'crit_dmg_skill': 25,
 'atk_caster_based_pct': 26,
 'split_dmg_pct': 27,
 'stun': 28,
 'fullburst_duration': 29,
 'attack_speed_pct': 30,
 'mg_warmup_speed_pct': 31}}

NAMED_MAGNITUDE = {'dmg_scale_mag_pct': 78, 'atk_buff_mag_pct': 79,
                   'received_dmg_buff_mag_pct': 80}

EXTRA_STAT = {'burst_cooldown': 32,
 'max_ammo_flat': 33,
 'charge_time_flat': 34,
 'pierce_dmg_pct': 35,
 'pierce_enabled': 36,
 'charge_speed_caster_based_pct': 37,
 'max_hp_pct': 38,
 'hp_caster_based_pct': 39,
 'hp_only_caster_based_pct': 40,
 'max_hp_only_pct': 41,
 'heal_received_pct': 42,
 'lifesteal_pct': 44,
 'shield_from_max_hp_pct': 45,
 'def_caster_based_pct': 46,
 'pellet_count': 47,
 'pellet_count_fixed': 48,
 'reload_ratio_pct': 49,
 'dot_dmg_pct': 50,
 'armor_break_dmg_pct': 51,
 'armor_break_enabled': 52,
 'charge_time_fixed': 53,
 'part_dmg_pct': 54,
 'intercept_dmg_pct': 55,
 'burst_dmg_aoe_pct': 56,
 'burst_dmg_single_pct': 57,
 'skill_cooldown_pct': 58,
 'infinite_ammo': 59,
 'burst_charge_speed_pct': 60,
 'optimal_range_min': 61,
 'optimal_range_max_pct': 62,
 'pierce_range': 63,
 'explosion_range': 64,
 'stealth': 65,
 'taunt': 66,
 'invincible': 67,
 'undying': 68,
 'received_dmg_split_even': 69,
 'cover_hp_pct': 70,
 'cover_disabled': 71,
 'decoy': 72,
 'outgoing_heal_pct': 73,
 'heal_overcharge_store': 74,
 'heal_split': 75,
 'heal_overcharge_store_atk_pct': 76,
 'accumulate_max_scale_pct': 77, **NAMED_MAGNITUDE,
 'dmg_accum_dealt_atk_pct': 81, 'dmg_accum_received_atk_pct': 82,
 'dmg_accum_rate_pct': 83, 'max_hp_from_max_hp_pct': 84,
 'atk_copy': 85, 'hp_copy': 86, 'target_hit_counter':87}

SCOPED_INERT = frozenset({'force_move', 'cover_def_pct', 'damage_reduction_pct'})
