"""Recipient admission; selector IDs and static masks come from detail_gpu.

Ranked recipients are admitted only for instants, which own no persistent carrier.
The runtime selects them from live GPU state at each activation.
"""
import re


def admitted(target, *, instant=False):
    if not isinstance(target, str):
        return False
    if target in ('self', 'all_allies', 'all_allies_excl_self', 'allies_squad', 'allies_burst3'):
        return True
    static = (r'allies_(?:right|adjacent):[1-5]', r'allies:[0-5]',
              r'allies_class:[^:]+(?::[0-5])?',
              r'allies_(?:weapon|code)(?:_excl_self)?:[^:]+',
              r'allies_code_weapon:[^:]+:[^:]+',
              r'allies_top_base_charge_time:[0-5]')
    if any(re.fullmatch(pattern, target) for pattern in static):
        return True
    if target in ('all_allies_burst_casted','all_allies_burst_not_casted') or re.fullmatch(r'allies_burst_casted_weapon:[^:]+',target) or re.fullmatch(r'allies_(?:with|without)_buff:.*',target):
        return True
    if not instant:
        return False
    return (target in ('all_allies_burst_casted', 'all_allies_burst_not_casted') or
            bool(re.fullmatch(r'allies_burst_casted_weapon:[^:]+', target)) or
            bool(re.fullmatch(r'allies_(?:top_atk(?:_excl)?|lowest_hp(?:_excl)?|top_def|lowest_atk_burst3):[1-5]', target)) or
            bool(re.fullmatch(r'allies_weapon_top_atk:[^:]+:[1-5]', target)))


def pack(words, index, row, limits, effect, stat_key, merge_search):
    kind = int(row[4])
    if kind not in (0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16):
        raise ValueError('Unported compiled recipient selector')
    at = limits['RECIPIENT_BASE'] + index * 8
    independent_quantity=effect.get('_source_tag')=='equipment' and int(row[2]) in (18,20,37)
    words[at:at+8] = [kind, 0 if kind in (12,13) else int(row[5]), int(row[48]),
                      int(row[223]) if kind in (12,13) else int(row[49]),
                      int(row[140]) if row[141] else 0,
                      int(row[5]) if kind in (12,13) else 0, stat_key,
                      int(bool(row[205]) and bool(effect.get('name')) and not independent_quantity) | (int(merge_search)<<1)]
