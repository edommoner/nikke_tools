"""Exact mode/enemy-name membership, physical damage and native controller state."""
from portable_named_state_oracle import observe as observe_named,compare as compare_named

def observe(case):
    return observe_named(dict(case,mode_session_reference=True))

def compare(case,gpu,contains):
    native=compare_named(dict(case,mode_session_reference=True),gpu,contains)
    assert len(gpu['queries'])==len(native['queries'])==4,case['name']
    contains(native['queries'],case['expected_queries'],case['name']+'.authored-domain-damage')
    return native
