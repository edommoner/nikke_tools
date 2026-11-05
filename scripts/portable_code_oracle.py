"""The actual native condition and activation paths, evaluated after readback."""
from portable_instant_list_oracle import compare as compare_allies
from portable_protection_oracle import observe as observe_allies
from portable_stack_oracle import compare as compare_enemies
from portable_removal_oracle import observe as observe_enemies
def observe(case):return observe_enemies(case) if case.get('code_enemy_reference') else observe_allies(case)
def compare(case,gpu,contains):
    return compare_enemies(case,gpu,contains) if case.get('code_enemy_reference') else compare_allies(case,gpu,contains)
