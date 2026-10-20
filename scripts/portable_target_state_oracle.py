"""Actual native enemy resolution and state gates; run after GPU readback."""
from portable_enemy_oracle import observe as observe_enemy


def observe(case):
    result = observe_enemy(dict(case,periodic_reference=True))
    return dict(queries=result['queries'])


def compare(case, gpu, contains):
    native = observe(case)
    contains(native['queries'], case['expected_queries'], case['name'] + '.authored_native')
    contains(gpu, native, case['name'] + '.native_target_state')
    return native
