"""Scalar damage contract shared by the portable packer and Slang schema.
Stat identities remain the existing effect compiler's identities.
"""
from effect_spec import DETAIL_STAT, EXTRA_STAT

BUFFS=frozenset(('pierce_enabled','armor_break_enabled','optimal_range_min','optimal_range_max_pct','lifesteal_pct','infinite_ammo','fullburst_duration','cover_hp_pct','burst_cooldown','invincible','undying','received_dmg_pct','def_pct','def_caster_based_pct','max_hp_pct','max_hp_only_pct','hp_caster_based_pct','hp_only_caster_based_pct','max_hp_from_max_hp_pct','heal_received_pct','outgoing_heal_pct','atk_pct','atk_caster_based_pct','def_ignore_pct','crit_rate','crit_dmg',
    'max_ammo_pct','max_ammo_flat','charge_speed_pct','charge_speed_caster_based_pct','charge_time_flat','charge_time_fixed',
    'charge_speed_buff_immune','charge_speed_debuff_immune','charge_speed_overflow_conversion_pct',
    'attack_speed_pct','mg_warmup_speed_pct','reload_speed_pct','reload_ratio_pct','accuracy_pct',
    'core_dmg_pct','charge_dmg_pct','charge_dmg_mag_pct','atk_dmg_pct',
    'normal_atk_dmg_pct','burst_dmg_pct','sequential_dmg_pct',
    'projectile_attachment_dmg_pct','projectile_explosion_dmg_pct','element_bonus_pct','element_bonus',
    'normal_atk_crit_rate','normal_atk_crit_dmg','split_dmg_pct','pierce_dmg_pct',
    'dot_dmg_pct','armor_break_dmg_pct','part_dmg_pct','intercept_dmg_pct',
    'burst_dmg_aoe_pct','burst_dmg_single_pct'))
BUFFS=BUFFS | {'burst_charge_speed_pct'}
STATS={k:v for k,v in {**DETAIL_STAT,**EXTRA_STAT}.items() if k in BUFFS or k in ('lifesteal_pct','atk_flat','element_bonus','crit_rate_skill','crit_dmg_skill','enemy_def_down_pct','enemy_def_down_flat','received_dmg_pct')}
DAMAGE_FAMILIES=frozenset(('damage','bonus_damage','burst_damage','split_damage','dot_damage',
    'auto_damage','armor_break_damage','armor_break_burst_damage','sequential_damage',
    'projectile_attachment_damage','projectile_explosion_damage','pierce_damage','core_damage'))
FLAGS=dict(NAMED_SKILL=131072,BURST=1,SEQUENTIAL=2,ATTACHMENT=4,EXPLOSION=8,SPLIT=16,CHARGE=32,
    PIERCE=64,DOT=128,ARMOR=512,PART=1024,INTERCEPT=2048,AOE_BURST=4096,
    SINGLE_BURST=8192,CORE=16384)

# Non-numeric presence marker; excluded from the64-entry numeric stat vector.
from portable_element_specs import STAT as ELEMENT_OVERRIDE_STAT
BUFFS=BUFFS | {'element_code_override'}
STATS['element_code_override']=ELEMENT_OVERRIDE_STAT

# Native late pass;never index the64-value vector with this identity.
from portable_hp_attack_specs import STAT as HP_ATTACK_STAT
BUFFS=BUFFS | {'atk_from_hp_pct'}
STATS['atk_from_hp_pct']=HP_ATTACK_STAT

# Presence markers retain the canonical compiler identities outside64 numeric slots.
BUFFS=BUFFS | {'taunt','stealth'}
STATS.update({name:{**DETAIL_STAT,**EXTRA_STAT}[name] for name in ('stealth','taunt')})

# Absolute reload-time values live outside the numeric damage vector.
from portable_reload_specs import STAT as RELOAD_FIXED_STAT
BUFFS=BUFFS | {'reload_time_fixed'}
STATS['reload_time_fixed']=RELOAD_FIXED_STAT

# Physical weapon modifiers; explosion range never indexes the64-value vector.
from portable_projectile_specs import STATS as PROJECTILE_STATS
BUFFS=BUFFS | PROJECTILE_STATS.keys()
STATS.update(PROJECTILE_STATS)

# Presence is read by the common status executor, not a damage multiplier.
BUFFS=BUFFS | {'stun'}
STATS['stun']={**DETAIL_STAT,**EXTRA_STAT}['stun']

# A typed overheal object, never a numeric damage-vector entry.
BUFFS=BUFFS | {'heal_overcharge_store'}
STATS['heal_overcharge_store']=EXTRA_STAT['heal_overcharge_store']

# Native periodic-skill interval percentage, not a one-shot remaining-time cut.
BUFFS=BUFFS | {'skill_cooldown_pct'}
STATS['skill_cooldown_pct']=EXTRA_STAT['skill_cooldown_pct']
