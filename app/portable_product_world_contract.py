"""Static world requirements, never a simulated schedule or numeric default."""
import copy

def has_incoming_attacks(prepared):
    from calculator.boss_pattern import validate
    patterns=validate(copy.deepcopy(prepared['enemy'].get('patterns',[])))
    # All literal attack nodes count, including delayed/unreachable ones. Do not
    # simulate triggers or infer that an attack will miss/land outside a battle.
    return any(p.attack is not None or p.summon is not None and p.summon.attack is not None for p in patterns)
