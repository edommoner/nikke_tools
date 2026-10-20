"""Native actual buff activation/query boundaries for the next geometry port."""
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / f) for f in ['app', 'scripts', 'tests']]
from test_target_counter_runtime import manager, NAMES
from calculator.buff_manager import optimal_range_of, _NIKKE


def effect(name, stat, value, timing='battle_start', conditions=None, duration=-1):
    return dict(name=name, source='스킬1', type='buff', stat=stat, fixed_value=value,
                duration=duration, target='self',
                trigger=dict(timing=[timing], condition=conditions or []))


def main():
    owner = next(i for i, n in enumerate(NAMES) if optimal_range_of(n, _NIKKE[n]['weapon_type'])[0] > 0)
    name = NAMES[owner]
    lo, hi = optimal_range_of(name, _NIKKE[name]['weapon_type'])
    rows = []
    for minimum, maximum in [(0, 0), (50, 0), (100, 0), (150, 0), (0, 20), (0, 100), (50, 20)]:
        lower = max(0., lo * (1. - minimum / 100.))
        upper = hi * (1. + maximum / 100.)
        for distance, expected in [(lower - 2e-9, False), (lower, True), (upper, True), (upper + 2e-9, False)]:
            mark = effect('mark', 'atk_pct', 1, 'on_attack', ['optimal_range'])
            bm = manager([effect('min', 'optimal_range_min', minimum),
                          effect('max', 'optimal_range_max_pct', maximum), mark], [owner]*3)
            bm.state['enemy'] = dict(distance=distance)
            bm.notify('battle_start', 0, name)
            actual = bm.get_buffs(name, '__enemy__', 0)
            assert actual['optimal_range_min_pct'] == minimum and actual['optimal_range_max_pct'] == maximum
            bm.notify('on_attack', .1, name)
            value = bm.get_buffs(name, '__enemy__', .1)['atk_pct']
            assert bool(value) == expected
            rows.append(dict(minimum_pct=minimum, maximum_pct=maximum, distance=distance,
                             lower=lower, upper=upper, marker_value=value, passed=expected))
    expiry = []
    for when, expected in [(.999999, True), (1., False), (1.000001, False)]:
        mark = effect('mark', 'atk_pct', 1, 'on_attack', ['optimal_range'])
        bm = manager([effect('min', 'optimal_range_min', 50, duration=1), mark], [owner]*2)
        bm.state['enemy'] = dict(distance=lo*.5)
        bm.notify('battle_start', 0, name)
        # No tick:query-time expiration must suffice,matching the native path.
        bm.notify('on_attack', when, name)
        value = bm.get_buffs(name, '__enemy__', when)['atk_pct']
        assert bool(value) == expected
        expiry.append(dict(time=when, marker_value=value, passed=expected))
    runtime = []
    for condition, initial, changed in [('optimal_range', dict(distance=lo), dict(distance=hi+1)),
                                         ('core_hit', dict(core_px=1), dict(core_px=0))]:
        bm = manager([effect('mark', 'atk_pct', 1, 'on_attack', [condition])], [owner])
        bm.state['enemy'] = initial
        bm.notify('on_attack', 0, name)
        bm.state['enemy'] = changed
        value = bm.get_buffs(name, '__enemy__', .1)['atk_pct']
        assert value == 1
        runtime.append(dict(condition=condition, initial_enemy=initial, changed_enemy=changed, marker_value=value))
    ordered = []
    for conditions, count in [(['optimal_range', 'prob:0'], 1), (['prob:0', 'optimal_range'], 0)]:
        bm = manager([effect('mark', 'atk_pct', 1, 'on_attack', conditions)], [owner])
        bm.state.update(enemy=dict(distance=lo), rng_expected=True)
        with patch.object(bm, 'get_buffs', wraps=bm.get_buffs) as query:
            e = bm._effects[0][0]
            passed = bm._condition_ok(conditions, name, 0, e)
            assert not passed and query.call_count == count
            ordered.append(dict(conditions=conditions, actual_queries=query.call_count, passed=passed))
    files = ['research/characterize-live-range.py', 'tests/test_target_counter_runtime.py',
             'app/engine_worker.py', 'app/engine_compat.py',
             'research/upstream/nikke-calc-master/calculator/buff_manager.py']
    report = dict(passed=True, cpu_only=True, gpu_execution_performed=False, gpu_admission_enabled=False,
        character=name, owner=owner, original_range=[lo, hi], range_buff_cases=rows,
        expiry_without_tick=expiry, runtime_queries_skip_activation_geometry=runtime, ordered_queries=ordered,
        scope='Real BuffManager buffs and notifications;only wraps count queries,no mocked buff values;not GPU proof',
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
    (ROOT/'research/portable-live-range-native.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('Native actual range buffs28,query expiry3,runtime geometry2,short-circuit2 verified')


if __name__ == '__main__':
    main()
