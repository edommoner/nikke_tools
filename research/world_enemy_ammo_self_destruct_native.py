"""Observe original combat through the common magazine and actor providers."""
from enemy_ammo_self_destruct_model import self_destruct_enemy_ammo
from world_logical_geometry_native import observe as logical_battle


def observe(case):
    with self_destruct_enemy_ammo(case['enemy_ammo']) as data:native,trace=logical_battle(case)
    native['enemy_ammo']=data
    return native,trace
