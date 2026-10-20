"""Characterize skill-level lookup and observable condition order on CPU only."""
import hashlib
import json
import struct
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / d) for d in ['app', 'scripts', 'tests', 'research']]
from test_target_counter_runtime import manager, NAMES


def effect(conditions):
    return dict(name='probability-value', type='buff', source='스킬2', stat='atk_pct',
                fixed_value=1, target='self', duration=-1,
                trigger=dict(timing=['on_attack'], condition=conditions))


def skill_case(name, values, levels, source, expected, skill_level=None):
    conditions = ['prob:{0}']
    authored = effect(conditions)
    authored.update(trigger_values=values, source=source)
    bm = manager([authored])
    char = bm._char[NAMES[0]]
    char['skill_levels'] = levels
    if skill_level is not None:
        char['skill_level'] = skill_level
    bm.state['rng_expected'] = True
    compiled = bm._effects[0][0]
    observed = []
    accumulators = []
    for i in range(len(expected)):
        observed.append(bm._condition_ok(conditions, NAMES[0], i / 60, compiled))
        accumulators.append(bm.state.get('rng_acc', {}).get(('prob', id(compiled), NAMES[0]), 0))
    assert observed == expected, (name, observed, expected)
    return dict(name=name, trigger_values=values, skill_levels=levels, source=source,
                skill_level=skill_level, passed=observed, accumulators=accumulators)


def main():
    cases = [
        skill_case('skill2-level3', {'3': 50, '10': 100}, {'1': 10, '2': 3}, '스킬2', [False, True] * 4),
        skill_case('missing-level-fallback10', {'10': 20}, {'2': 3}, '스킬2', [False] * 4 + [True]),
        skill_case('missing-level-in-skill-map-default10', {'10': 100}, {'1': 4}, '스킬2', [True] * 3),
        skill_case('skill1-selects-own-level', {'3': 50, '10': 100}, {'1': 3, '2': 10}, '스킬1', [False, True]),
        skill_case('global-skill-level-fallback', {'5': 50, '10': 100}, {}, 'unknown', [False, True], 5),
        skill_case('empty-values-no-accumulation', {}, {'2': 10}, '스킬2', [False] * 4),
    ]
    rows = []
    for conditions, expected_queries, expected_accumulator in [
        (['self_stat_above:atk_pct:1', 'prob:20'], 1, 0),
        (['prob:20', 'self_stat_above:atk_pct:1'], 0, .2),
        (['self_stat_above:atk_pct:1', 'prob:100'], 1, 0),
        (['prob:100', 'self_stat_above:atk_pct:1'], 1, 0),
    ]:
        bm = manager([effect(conditions)])
        bm.state['rng_expected'] = True
        compiled = bm._effects[0][0]
        with patch.object(bm, 'get_buffs', return_value={}) as query:
            observed = bm._condition_ok(conditions, NAMES[0], 0, compiled)
        accumulator = bm.state.get('rng_acc', {}).get(('prob', id(compiled), NAMES[0]), 0)
        assert not observed and query.call_count == expected_queries and accumulator == expected_accumulator
        rows.append(dict(conditions=conditions, passed=observed, stat_queries=query.call_count,
                         accumulator=accumulator, accumulator_hex=accumulator.hex() if isinstance(accumulator, float) else float(accumulator).hex()))
    # Native squad-hit listeners evaluate conditions as the definition owner,
    # then activate as the actual attacker. Alternate attackers must therefore
    # share the source owner's probability phase for this one effect instance.
    authored = effect(['prob:50'])
    authored['trigger']['timing'] = ['body_hit_count:1']
    bm = manager([authored])
    bm.state['rng_expected'] = True
    compiled = bm._effects[0][0]
    with patch.object(bm, '_activate') as activate:
        for i, attacker in enumerate(NAMES[:4]):
            bm.notify_team_hit('squad_body_hit', i / 60, attacker)
    attackers = [call.args[1] for call in activate.call_args_list]
    assert attackers == [NAMES[1], NAMES[3]], attackers
    accumulators = bm.state['rng_acc']
    assert set(accumulators) == {('prob', id(compiled), NAMES[0])}
    team = dict(effect_owner=NAMES[0], attackers=NAMES[:4], activated_as=attackers,
                accumulator_owner=NAMES[0], accumulator=accumulators[('prob', id(compiled), NAMES[0])])
    long_phases = []
    for conditions in [['prob:10'], ['prob:20'], ['prob:33.3333'], ['prob:50', 'prob:50'], ['prob:10', 'prob:100']]:
        bm = manager([effect(conditions)])
        bm.state['rng_expected'] = True
        compiled = bm._effects[0][0]
        digest = hashlib.sha256()
        fired = []
        for i in range(4096):
            passed = bm._condition_ok(conditions, NAMES[0], i / 60, compiled)
            accumulator = bm.state['rng_acc'][('prob', id(compiled), NAMES[0])]
            digest.update(struct.pack('<Bd', passed, accumulator))
            if passed:
                fired.append(i + 1)
        if conditions == ['prob:10']:
            assert fired == list(range(11, 4097, 10))
        if conditions == ['prob:20']:
            assert fired == list(range(5, 4097, 5))
        if conditions == ['prob:50', 'prob:50']:
            assert not fired
        long_phases.append(dict(conditions=conditions, events=4096, fires=len(fired),
                                first_fires=fired[:16], last_fires=fired[-4:],
                                final_accumulator_hex=float(accumulator).hex(),
                                final_accumulator_bits=struct.pack('<d', accumulator).hex(),
                                passed_and_binary64_state_sha256=digest.hexdigest(),
                                digest_layout='per event: uint8 passed followed by little-endian binary64 accumulator'))
    files = ['research/characterize-probability-values.py', 'tests/test_target_counter_runtime.py',
             'app/engine_worker.py', 'app/engine_compat.py',
             'research/upstream/nikke-calc-master/calculator/buff_manager.py']
    result = dict(passed=True, cpu_only=True, gpu_admission_enabled=False,
                  skill_value_cases=cases, condition_order_cases=rows, squad_hit_owner_phase=team,
                  long_binary64_phases=long_phases,
                  rules=['Resolve trigger_values by the effect source skill level; fall back to key10 when that level is absent',
                         'An empty trigger_values mapping returns false without advancing an accumulator',
                         'A failed stat condition before probability prevents its accumulator advance',
                         'A failed probability condition before stat prevents the stat query',
                         'Squad-hit listeners share the source-owner probability phase across actual attackers',
                         'GPU activation must evaluate stateful probability and stat queries in authored order'],
                  source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files})
    (ROOT / 'research/portable-probability-values-native.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('CPU skill-level probability values and authored short-circuit query order verified')


if __name__ == '__main__':
    main()
