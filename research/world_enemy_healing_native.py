"""Existing complete logical battle observer plus declared real ADD healing."""
from enemy_healing_model import enemy_healing
from world_logical_geometry_native import observe as logical_battle

def observe(case):
    with enemy_healing(case['enemy_healing']) as healing:native,trace=logical_battle(case)
    native['enemy_healing']=healing
    return native,trace
