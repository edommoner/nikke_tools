"""Fail closed for reference-engine keys whose GPU consumers are not ported."""


class UnsupportedEngineKeys(ValueError):
    pass


def require_supported(effects, cubes=()):
    keys = set()
    def rows(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from rows(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                yield from rows(child)

    for effect in rows(list(effects)):
        for field, values in (
            ('target', {'self_and_engaged_allies', 'allies_down_all'}),
            ('stat', {'engaged_state', 'normal_atk_width_pct'}),
        ):
            value = effect.get(field)
            if isinstance(value, str) and value in values:
                keys.add(field + ':' + value)
        conditions = effect.get('condition', [])
        if isinstance(conditions, str):
            conditions = [conditions]
        for condition in conditions:
            if condition == 'during_full_charge' or condition.startswith(('ally_down_count_above:', 'ally_down_count_below:')):
                keys.add('condition:' + condition)
    if '렐릭 베젤 큐브' in cubes:
        keys.update(('cube:렐릭 베젤 큐브', 'stat:hp_only_caster_based_pct', 'timing:full_burst_start', 'max_stack:3'))
    if keys:
        raise UnsupportedEngineKeys('Unsupported GPU reference engine keys: ' + ', '.join(sorted(keys)))
