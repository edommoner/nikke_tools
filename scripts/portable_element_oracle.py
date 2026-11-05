"""Actual native CharState.element_match plus damage/routing after readback."""
from portable_enemy_oracle import observe as observe_packets

def observe(case):
    if case.get('element_physical_reference'):
        from portable_weapon_oracle import observe as observe_weapon
        queries,timings=observe_weapon(case);return dict(queries=queries,weapon_timings=timings)
    return observe_packets(case)

def compare(case,gpu,contains):
    cpu=observe(case)
    contains(cpu['queries'],case['expected_queries'],case['name']+'.authored-expectations')
    contains(gpu['queries'],cpu['queries'],case['name']+'.native-element-damage')
    if case.get('element_physical_reference'):
        contains(gpu['weapons'][0],cpu['weapon_timings'],case['name']+'.native-physical-clock');return cpu
    contains(gpu['target_scored_damage'],cpu['target_scored_damage'],case['name']+'.native-target-scores')
    assert len(gpu['trace'])==len(cpu['packets']),(case['name'],'packet count')
    contains(gpu['trace'],cpu['packets'],case['name']+'.native-packets')
    return cpu
