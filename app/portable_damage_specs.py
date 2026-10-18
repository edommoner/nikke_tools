"""Scalar damage contract shared by the portable packer and Slang schema.
Stat identities remain the existing effect compiler's identities.
"""
from effect_spec import DETAIL_STAT, EXTRA_STAT

BUFFS=frozenset(('atk_pct','atk_caster_based_pct','def_ignore_pct','crit_rate','crit_dmg',
    'attack_speed_pct','mg_warmup_speed_pct','reload_speed_pct','reload_ratio_pct','accuracy_pct',
    'core_dmg_pct','charge_dmg_pct','charge_dmg_mag_pct','atk_dmg_pct',
    'normal_atk_dmg_pct','burst_dmg_pct','sequential_dmg_pct',
    'projectile_attachment_dmg_pct','projectile_explosion_dmg_pct','element_bonus_pct',
    'normal_atk_crit_rate','normal_atk_crit_dmg','split_dmg_pct','pierce_dmg_pct',
    'dot_dmg_pct','armor_break_dmg_pct','part_dmg_pct','intercept_dmg_pct',
    'burst_dmg_aoe_pct','burst_dmg_single_pct'))
STATS={k:v for k,v in {**DETAIL_STAT,**EXTRA_STAT}.items() if k in BUFFS or k in ('atk_flat','element_bonus','crit_rate_skill','crit_dmg_skill','enemy_def_down_pct','enemy_def_down_flat','received_dmg_pct')}
DAMAGE_FAMILIES=frozenset(('damage','bonus_damage','burst_damage','split_damage','dot_damage',
    'auto_damage','armor_break_damage','armor_break_burst_damage','sequential_damage',
    'projectile_attachment_damage','projectile_explosion_damage','pierce_damage','core_damage'))
FLAGS=dict(BURST=1,SEQUENTIAL=2,ATTACHMENT=4,EXPLOSION=8,SPLIT=16,CHARGE=32,
    PIERCE=64,DOT=128,ARMOR=512,PART=1024,INTERCEPT=2048,AOE_BURST=4096,
    SINGLE_BURST=8192,CORE=16384)
