"""Recipient admission; selector IDs and static masks come from detail_gpu.

Ranked buff recipients resolve once on first consumption. Instants resolve at
each activation. Selection and shared snapshots are entirely GPU owned.
"""
import re


def admitted(target, *, instant=False):
    if isinstance(target,list):
        def leaves(items):
            for item in items:
                if isinstance(item,list):yield from leaves(item)
                else:yield item
        flat=list(leaves(target))
        return 1<=len(flat)<=21 and all(admitted(item,instant=instant) for item in flat)
    if not isinstance(target, str):
        return False
    if instant and re.fullmatch(r'allies_down_(?:top_atk_excl:[1-5]|class_random:[^:]+:[1-5])',target):return True
    if re.fullmatch(r'allies_lowest_cover_hp:[1-5]',target):return True
    from portable_ally_random_specs import contains
    if contains(target):return True
    if target in ('self', 'all_allies', 'all_allies_excl_self', 'allies_squad', 'allies_burst3', 'allies_burst_casted_burst3', 'allies_burst3_persona_excl_self', 'allies_below_def'):
        return True
    static = (r'allies_(?:right|adjacent):[1-5]', r'allies:[0-5]',
              r'allies_class:[^:]+(?::[0-5])?',
              r'allies_(?:weapon|code)(?:_excl_self)?:[^:]+',
              r'allies_code_weapon:[^:]+:[^:]+',
              r'allies_code_weapon_leftmost:[^:]+:[^:]+:[0-5]',
              r'allies_top_base_charge_time:[0-5]')
    if any(re.fullmatch(pattern, target) for pattern in static):
        return True
    if target in ('all_allies_burst_casted','all_allies_burst_not_casted') or re.fullmatch(r'allies_burst_casted_weapon:[^:]+',target) or re.fullmatch(r'allies_(?:with|without)_buff:.*',target):
        return True
    if (re.fullmatch(r'allies_(?:top_atk(?:_excl)?|lowest_hp(?:_excl)?|top_def|lowest_atk_burst3):[1-5]', target) or
        re.fullmatch(r'allies_weapon_top_atk:[^:]+:[1-5]', target)):
        return True
    # The canonical compiler already lowers literal identities to selector8.
    # Keep catalog validation here; execution consumes the same static mask.
    from calculator.buff_manager import _NIKKE
    return target in _NIKKE


def pack(words, index, row, limits, effect, stat_key, merge_search, lazy_group):
    kind = int(row[4])
    # The native broken-cover selector is eager; retain other group IDs.
    if kind==25:lazy_group=0
    from portable_enemy_specs import enemy_buff_plan
    enemy = enemy_buff_plan(effect) is not None
    if enemy:kind=4
    if kind not in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25):
        raise ValueError('Unported compiled recipient selector')
    at = limits['RECIPIENT_BASE'] + index * 8
    independent_quantity=effect.get('_source_tag')=='equipment' and int(row[2]) in (18,20,37)
    from calculator.buff_manager import _STAT_TO_BUFF
    query_resolve=effect.get('type')=='buff' and bool(_STAT_TO_BUFF.get(effect.get('stat')))
    flags=int(bool(row[205]) and bool(effect.get('name')) and not independent_quantity) | (int(merge_search)<<1) | (int(query_resolve)<<2)
    if kind==17:
        first=int(row[5])-limits['_AUTHORED_DEFINITIONS']
        words[at:at+8]=[17,int(row[48]),first,0,0,0,stat_key,flags]
        return
    words[at:at+8] = [kind, 0 if kind in (4,12,13) else int(row[5]), 0 if kind==4 else int(row[48]),
                      int(row[223]) if kind in (12,13) else int(row[49]),
                      int(row[140]) if row[141] else 0,
                      int(row[5]) if kind in (12,13) else 0, stat_key,
                      flags | (lazy_group<<4)]
