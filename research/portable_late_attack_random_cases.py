"""Late attack selectors use fresh direct reads; ordinary mapped stats use lazy membership."""
import copy
from portable_ally_random_reference_cases import fixtures as random_fixtures
from world_enemy_attack_cases import field


def fixtures():
    base = copy.deepcopy(random_fixtures()[0])
    base.pop('contract')
    rows = []
    for label, stat, extra in (
        ('caster', 'atk_caster_based_pct', None),
        ('caster-hp-pass', 'atk_caster_based_pct', 'atk_from_hp_pct'),
        ('hp', 'atk_from_hp_pct', None),
        ('mapped-control', 'def_pct', None),
        ('caster-mapped-sibling', 'atk_caster_based_pct', 'def_pct'),
    ):
        case = copy.deepcopy(base)
        case['name'] = 'late-attack-random-' + label
        case['effects'][1].update(stat=stat, duration=-1)
        case['effects'][1]['trigger']['timing'] = ['battle_start']
        # Owner4 casts the buff; the firing owner0 is an eligible recipient.
        case['owners'][1] = 4
        if extra:
            target = 'allies_random:1' if extra == 'def_pct' else 'self'
            case['effects'].append(field(extra, 1, target, 'late-pass-sibling', duration=-1))
            case['owners'].append(4)
        rows.append(case)
    return rows
