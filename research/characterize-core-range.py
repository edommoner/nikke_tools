"""CPU-only native core/range predicates for the next unadmitted families."""
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / folder) for folder in ['app', 'scripts', 'tests']]
from test_target_counter_runtime import manager, NAMES
from calculator import buff_manager


def effect(conditions):
    return dict(name='geometry-condition', source='스킬1', type='buff', stat='atk_pct',
                fixed_value=1, duration=-1, target='self',
                trigger=dict(timing=['on_attack'], condition=conditions))


def evaluate(conditions, enemy, owner=0, buffs=None, changed_weapon=None):
    bm = manager([effect(conditions)], [owner])
    bm.state['enemy'] = enemy
    bm.state['rng_expected'] = True
    if changed_weapon:
        bm.state['weapon_change'] = {NAMES[owner]: dict(weapon_type=changed_weapon)}
    authored = bm._effects[0][0]
    with patch.object(bm, 'get_buffs', return_value=buffs or {}) as query:
        passed = bm._condition_ok(conditions, NAMES[owner], 0, authored)
    return dict(conditions=conditions, enemy=enemy, owner=owner, roster_weapon=buff_manager._NIKKE[NAMES[owner]]['weapon_type'],
                changed_weapon=changed_weapon, buffs=buffs or {}, passed=passed, stat_queries=query.call_count,
                probability_accumulator=bm.state['rng_acc'].get(('prob', id(authored), NAMES[owner]), 0))


def main():
    core = []
    for value, expected in [(0, False), (.5, False), (1, True), (2, True)]:
        row = evaluate(['core_hit'], dict(core_px=value))
        assert row['passed'] == expected and row['stat_queries'] == 0
        core.append(row)
    ordered = [evaluate(['core_hit', 'prob:20'], dict(core_px=0)),
               evaluate(['prob:20', 'core_hit'], dict(core_px=0))]
    assert ordered[0]['probability_accumulator'] == 0 and ordered[1]['probability_accumulator'] == .2
    owner = next(i for i, name in enumerate(NAMES)
                 if buff_manager.optimal_range_of(name, buff_manager._NIKKE[name]['weapon_type'])[0] > 0)
    name = NAMES[owner]
    weapon = buff_manager._NIKKE[name]['weapon_type']
    lo, hi = buff_manager.optimal_range_of(name, weapon)
    rows = []
    for enemy, changed, expected in [({}, None, False), (dict(optimal_range_weapons=[weapon]), None, True),
                                     (dict(optimal_range_weapons=[weapon]), 'RL', True)]:
        row = evaluate(['optimal_range'], enemy, owner, changed_weapon=changed)
        assert row['passed'] == expected and row['stat_queries'] == 0
        rows.append(row)
    for distance, expected in [(lo - 2e-9, False), (lo - 5e-10, True), (lo, True),
                               (hi, True), (hi + 5e-10, True), (hi + 2e-9, False)]:
        row = evaluate(['optimal_range'], dict(distance=distance), owner)
        assert row['passed'] == expected and row['stat_queries'] == 1
        rows.append(row)
    buffs = dict(optimal_range_min_pct=50, optimal_range_max_pct=20)
    for distance in [lo * .5, hi * 1.2]:
        row = evaluate(['optimal_range'], dict(distance=distance), owner, buffs)
        assert row['passed'] and row['stat_queries'] == 1
        rows.append(row)
    for conditions, count in [(['self_state:absent', 'optimal_range'], 0),
                              (['optimal_range', 'self_state:absent'], 1),
                              (['prob:0', 'optimal_range'], 0), (['optimal_range', 'prob:0'], 1)]:
        row = evaluate(conditions, dict(distance=(lo + hi) / 2), owner)
        assert not row['passed'] and row['stat_queries'] == count
        rows.append(row)
    files = ['research/characterize-core-range.py', 'app/engine_worker.py', 'app/engine_compat.py',
             'tests/test_target_counter_runtime.py', 'research/upstream/nikke-calc-master/calculator/buff_manager.py',
             'research/upstream/nikke-calc-master/data/parsed_nikke.json']
    result = dict(passed=True, cpu_only=True, gpu_execution_performed=False, gpu_admission_enabled=False,
                  core_cases=core, core_probability_order=ordered, range_cases=rows,
                  native_range=dict(character=name, owner=owner, weapon=weapon, minimum=lo, maximum=hi),
                  rules=['core_hit uses global enemy.core_px >=1, independently of actual core impact outcome',
                         'optimal_range uses immutable roster weapon type even while a weapon mode is active',
                         'No distance uses explicit optimal_range_weapons membership without a buff query',
                         'Explicit distance queries current buffs and checks both endpoints with binary64 1e-9 slack',
                         'Minimum-range buff decreases lower bound;maximum-range buff increases upper bound',
                         'Authored short-circuit order determines whether the stat query or probability update happens'],
                  source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files})
    (ROOT / 'research/portable-core-range-native.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('Native core threshold and range/list/buff/order boundaries verified;GPU admission remains disabled')


if __name__ == '__main__':
    main()
