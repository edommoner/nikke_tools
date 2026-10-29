"""One original sampled battle plus declared live collider motion."""
from enemy_movement_model import enemy_movement
from world_logical_geometry_native import observe as logical_battle


def observe(case):
    with enemy_movement(case['enemy_movement']) as movement:native,trace=logical_battle(case)
    native['enemy_movement']=movement
    return native,trace
