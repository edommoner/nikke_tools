"""Authored real-battle contracts; no probabilities or GPU packets packed."""
from portable_coordinate_physical_cases import fixtures as physical_fixtures
import copy


def fixtures():
    rows = physical_fixtures()
    case = copy.deepcopy(rows[1])
    case['name'] = 'coordinate-physical-reference/threshold-snapshot'
    case['duration'] = .15
    case['combat']['weapons'][0].update(pellets=3, muzzles=2)
    from world_enemy_attack_cases import field
    case['effects'].append(field('atk_pct', 100, 'self', 'part-snapshot',
                                 'part_hit_count:1', max_stack=128))
    case['owners'].append(0)
    rows.append(case)
    return rows
