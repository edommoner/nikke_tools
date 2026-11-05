"""Literal enemy/weapon geometry;all range comparisons and buff queries stay GPU owned."""
import copy
import math

WEAPONS = {name: i+1 for i, name in enumerate(('AR', 'SMG', 'SG', 'SR', 'RL', 'MG'))}
CORE = 35
RANGE = 33
RANGE_STATS = frozenset(('optimal_range_min', 'optimal_range_max_pct'))


def required(effects):
    return any(e.get('stat') in RANGE_STATS or set(e.get('trigger', {}).get('condition', [])) & {'core_hit', 'optimal_range'} for e, _ in effects)


def number(value, *, nonnegative=False):
    if type(value) not in (int, float):
        raise ValueError('Geometry requires finite numeric input')
    try:finite=math.isfinite(value)
    except OverflowError:finite=False
    if not finite or nonnegative and value < 0:
        raise ValueError('Geometry requires finite numeric input')
    return value


def validate(geometry):
    if not isinstance(geometry, dict) or set(geometry)-{'core_px', 'distance', 'optimal_weapons', 'weapons'}:
        raise ValueError('Unsupported geometry fields')
    number(geometry.get('core_px', 0), nonnegative=True)
    if geometry.get('distance') is not None:
        number(geometry['distance'])
    selected = geometry.get('optimal_weapons', [])
    if not isinstance(selected, list) or any(not isinstance(w, str) or w not in WEAPONS for w in selected) or len(selected) != len(set(selected)):
        raise ValueError('Invalid optimal weapon list')
    if geometry.get('distance') is not None and selected:
        raise ValueError('Distance and optimal weapon list are mutually exclusive')
    weapons = geometry.get('weapons')
    if not isinstance(weapons, list) or len(weapons) != 5:
        raise ValueError('Geometry requires five original weapons')
    for w in weapons:
        if not isinstance(w, dict) or set(w) != {'type', 'minimum', 'maximum'} or not isinstance(w['type'], str) or w['type'] not in WEAPONS:
            raise ValueError('Invalid original weapon geometry')
        number(w['minimum'], nonnegative=True); number(w['maximum'], nonnegative=True)
        if w['minimum'] > w['maximum']:
            raise ValueError('Invalid range bounds')


def from_roster(chars, enemy):
    from calculator.buff_manager import optimal_range_of, _NIKKE
    weapons = []
    for c in chars:
        # Native activation predicates use roster identity,not an active mode.
        weapon = _NIKKE[c['name']]['weapon_type']
        lo, hi = optimal_range_of(c['name'], weapon)
        weapons.append(dict(type=weapon, minimum=lo, maximum=hi))
    return dict(core_px=enemy.get('core_px', 0) or 0, distance=enemy.get('distance'),
                optimal_weapons=copy.deepcopy(enemy.get('optimal_range_weapons') or []), weapons=weapons)


def compiler_chars(chars, geometry):
    if geometry is None:
        return chars
    validate(geometry)
    return [dict(c, _detail_enemy_core_px=geometry.get('core_px', 0),
                 _detail_range=[w['minimum'], w['maximum'], geometry.get('distance')])
            for c, w in zip(chars, geometry['weapons'])]


def pack(words, geometry, effects, rows, chars, L, double_words):
    if geometry is None:
        if required(effects):
            raise ValueError('Core/range effects require literal geometry input')
        return
    validate(geometry)
    at = L['GEOMETRY_BASE']
    words[at:at+2] = [1 | (2 if geometry.get('distance') is not None else 0),
                      sum(1 << (WEAPONS[w]-1) for w in geometry.get('optimal_weapons', []))]
    words[at+2:at+4] = double_words(geometry.get('core_px', 0))
    words[at+4:at+6] = double_words(geometry.get('distance') if geometry.get('distance') is not None else 0)
    for owner, w in enumerate(geometry['weapons']):
        pos = at+16+owner*8
        words[pos] = WEAPONS[w['type']]
        words[pos+2:pos+6] = double_words(w['minimum'])+double_words(w['maximum'])
    for index, ((e, _), row) in enumerate(zip(effects, rows)):
        if e.get('type') != 'weapon_change':
            continue
        weapon = e.get('weapon_type', 'SR')
        if weapon not in WEAPONS:
            raise ValueError('Invalid changed weapon geometry')
        lo, hi = row[264:266]
        number(lo, nonnegative=True); number(hi, nonnegative=True)
        if lo > hi:
            raise ValueError('Invalid changed range bounds')
        pos = at+56+index*6
        words[pos] = WEAPONS[weapon]
        words[pos+2:pos+6] = double_words(lo)+double_words(hi)
