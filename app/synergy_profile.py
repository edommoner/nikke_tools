"""Pure, data-derived roster synergy profiles."""

TIER_B_TRAITS = {
    'pierce_dmg_pct': 'pierce',
    'armor_break_dmg_pct': 'armor_break',
    'charge_dmg_pct': 'charge',
    'charge_speed_pct': 'charge',
    'charge_speed_caster_based_pct': 'charge',
    'charge_dmg_mag_pct': 'charge',
    'charge_time_flat': 'charge',
    'projectile_explosion_dmg_pct': 'explosion',
    'split_dmg_pct': 'split',
    'dot_dmg_pct': 'dot',
    'mg_warmup_speed_pct': 'mg',
    'pellet_count': 'sg',
}


def _selector(target, skills, stat):
    """Return (tier, selector), or None for non-ally targets."""
    rule, *params = target.split(':')
    excl = 'excl_self' in rule
    if target in skills:
        return 'A', {'kind': 'name', 'value': target}
    if rule in ('allies_code', 'allies_code_excl_self') and params:
        return 'A', {'kind': 'element', 'value': params[0], 'excl_self': excl}
    if rule in ('allies_weapon', 'allies_weapon_excl_self',
                'allies_burst_casted_weapon', 'allies_weapon_top_atk') and params:
        return 'A', {'kind': 'weapon', 'value': params[0], 'excl_self': excl}
    if rule == 'allies_class' and params:
        return 'A', {'kind': 'class', 'value': params[0]}
    if rule in ('allies_code_weapon', 'allies_code_weapon_leftmost') and len(params) >= 2:
        return 'A', {'kind': 'element_weapon', 'element': params[0], 'weapon': params[1]}
    if rule == 'allies_squad':
        return 'A', {'kind': 'squad'}
    if rule in ('allies_burst_casted_burst3', 'allies_lowest_atk_burst3'):
        return 'A', {'kind': 'burst', 'value': '3'}
    if rule == 'allies_burst3_persona_excl_self':
        return 'A', {'kind': 'squad_burst', 'value': '3', 'excl_self': True}
    if target in ('all_allies', 'all_allies_excl_self', 'all_allies_burst_casted',
                  'all_allies_burst_not_casted'):
        if stat in TIER_B_TRAITS:
            return 'B', {'kind': 'trait', 'value': TIER_B_TRAITS[stat], 'excl_self': excl}
        return 'C', {'kind': 'all', 'excl_self': excl}
    if target.startswith('allies_'):
        selector = {'kind': 'dynamic', 'rule': rule}
        if excl:
            selector['excl_self'] = True
        return 'C', selector
    return None


def _merge(entries, key, entry, effect):
    """Retain the first base provenance, falling back to the first favorite."""
    favorite = 'favorite' in effect
    previous = entries.get(key)
    if previous is None:
        entries[key] = {**entry, 'source': effect.get('source'),
                        'name': effect.get('name'), 'favorite': favorite}
    elif previous['favorite'] and not favorite:
        previous.update(source=effect.get('source'), name=effect.get('name'), favorite=False)


def build_profiles(skills: dict, meta: dict) -> dict:
    profiles = {}
    condition_rules = {
        'squad_ally_exists': ('squad_member', None, False),
        'has_burst1_ally': ('has_burst', '1', False),
        'no_burst1_ally': ('has_burst', '1', True),
        'has_defender_ally': ('has_class', '방어형', False),
        'no_defender_ally': ('has_class', '방어형', True),
    }
    for character, effects in skills.items():
        info = meta.get(character, {})
        traits, provides, conditions = set(), {}, {}
        if info.get('is_charge'):
            traits.add('charge')
        weapon = info.get('weapon_type')
        if weapon in ('MG', 'SG'):
            traits.add(weapon.lower())
        if weapon == 'RL':
            traits.add('explosion')
        for effect in effects:
            stat = effect.get('stat', '')
            if stat == 'pierce_enabled':
                traits.add('pierce')
            if stat == 'armor_break_enabled':
                traits.add('armor_break')
            if stat in ('explosion_range', 'projectile_explosion_dmg_pct'):
                traits.add('explosion')
            if stat == 'split_dmg_pct' or (effect.get('type') == 'damage' and 'split' in stat):
                traits.add('split')
            if stat == 'dot_dmg_pct' or (effect.get('type') == 'damage' and 'tick_interval' in effect):
                traits.add('dot')
            trigger = effect.get('trigger', {})
            for condition in trigger.get('condition', []):
                if condition in condition_rules:
                    kind, value, negate = condition_rules[condition]
                    entry = {'kind': kind, 'negate': negate}
                    if value is not None:
                        entry['value'] = value
                    _merge(conditions, (kind, value, negate), entry, effect)
            targets = effect.get('target', '')
            if isinstance(targets, str):
                targets = [targets]
            ally_targeted = False
            for target in targets:
                match = _selector(target, skills, stat)
                if match is None or effect.get('polarity') == 'harmful':
                    continue
                ally_targeted = True
                tier, selector = match
                key = (tier, tuple(sorted(selector.items())), stat)
                _merge(provides, key, {'tier': tier, 'selector': selector, 'stat': stat}, effect)
            if ally_targeted:
                for timing in trigger.get('timing', []):
                    if timing.startswith('squad_burst_cast:'):
                        value = timing.split(':', 1)[1]
                        _merge(conditions, ('has_burst', value, False),
                               {'kind': 'has_burst', 'value': value, 'negate': False}, effect)
        profiles[character] = {'traits': sorted(traits), 'provides': list(provides.values()),
                               'conditions': list(conditions.values())}
    return profiles
