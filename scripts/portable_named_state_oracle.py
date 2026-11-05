"""Exact-name state semantics in the actual native BuffManager/controller."""
from portable_instant_list_oracle import compare as compare_membership
from portable_burst_oracle import observe as observe_weapon
from portable_protection_oracle import observe as observe_buffs

def observe(case):
    return observe_weapon(case) if 'combat' in case else observe_buffs(case)

def compare(case, gpu, contains):
    if 'combat' not in case: return compare_membership(case,gpu,contains)
    native=observe_weapon(case)
    assert len(gpu['queries'])==len(native['queries'])
    contains(gpu['queries'],native['queries'],case['name']+'.native-controller')
    return native
