"""Observe native non-core expected accumulation; no GPU admission or execution."""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / n) for n in ('app', 'scripts', 'tests')]
from test_target_counter_runtime import manager, NAMES


def marker(conditions):
    return dict(name='non-core-study', source='스킬1', type='buff', stat='atk_pct',
                fixed_value=1, duration=-1, target='self',
                trigger=dict(timing=['on_attack'], condition=conditions))


def bits(value):
    return struct.pack('>d', value).hex()


def main():
    rows = []
    for owner in range(5):
        for fraction in (None, 0., .2, .5, .9, math.nextafter(1., 0.), 1.):
            conditions = ['not_core']
            bm = manager([marker(conditions)], [owner])
            bm.state['rng_expected'] = True
            eff = bm._effects[0][0]
            balance = 0.
            events = []
            for index in range(32):
                bm._notify_ctx = {} if fraction is None else dict(core_frac=fraction)
                expected = balance + (1. - (fraction or 0.))
                passed = expected >= 1.
                balance = expected - 1. if passed else expected
                actual = bm._condition_ok(conditions, NAMES[owner], index * .1, eff)
                value = bm.state['rng_acc'][('not_core', id(eff), NAMES[owner])]
                assert actual == passed and bits(value) == bits(balance)
                events.append(dict(passed=actual, balance=value, binary64=bits(value)))
            rows.append(dict(owner=owner, core_fraction=fraction, events=events))
    ordered = []
    for conditions in (['prob:0', 'not_core'], ['not_core', 'prob:0'],
                       ['prob:100', 'not_core'], ['not_core', 'prob:100']):
        bm = manager([marker(conditions)])
        bm.state['rng_expected'] = True
        bm._notify_ctx = dict(core_frac=.5)
        eff = bm._effects[0][0]
        actual = bm._condition_ok(conditions, NAMES[0], 0, eff)
        balances = {key[0]: dict(value=value, binary64=bits(value))
                    for key, value in bm.state['rng_acc'].items()}
        assert not actual
        assert ('not_core' in balances) == (conditions[0] != 'prob:0')
        if 'not_core' in balances:
            assert balances['not_core']['value'] == .5
        ordered.append(dict(conditions=conditions, passed=actual, balances=balances))
    paths = ['research/characterize-not-core.py', 'tests/test_target_counter_runtime.py',
             'app/engine_worker.py', 'app/engine_compat.py',
             'research/upstream/nikke-calc-master/calculator/buff_manager.py']
    result = dict(passed=True, cpu_only=True, gpu_execution_performed=False,
                  gpu_admission_enabled=False, full_character_verified=0,
                  cases=rows, authored_short_circuit=ordered,
                  findings=['not_core reads impact context core_frac, not enemy core diameter',
                            'missing core_frac means zero;expected mode accumulates 1-core_frac',
                            'accumulator key is distinct from prob and private to effect identity and caster'],
                  scope='35 native condition sequences x32 events plus4 authored order cases;no physical impact generation or GPU proof',
                  source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})
    (ROOT / 'research/portable-not-core-native.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Native not_core35 sequences/1120 events and4 short-circuit cases verified;GPU admission disabled')


if __name__ == '__main__':
    main()
