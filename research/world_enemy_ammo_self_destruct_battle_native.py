"""Reuse complete retirement, incoming and original resource observations."""
import copy
from enemy_ammo_self_destruct_model import self_destruct_enemy_ammo
from portable_enemy_ammo_self_destruct_wire import compile_battle
from portable_coordinate_original_cases import prepare_case as original_case
from world_add_self_destruct_battle_native import observe as self_observe


def prepare_case(row):
    case,prepared=original_case(row)
    case.update(logical_geometry=copy.deepcopy(row['logical_geometry']),enemy_ammo=copy.deepcopy(row['enemy_ammo']),
        enemy_ammo_contract=copy.deepcopy(row['contract']),sampled_groups=True)
    words,meta,bindings,scene=compile_battle(prepared,case['logical_geometry'],case['enemy_ammo'])
    return words,(case,meta,bindings,scene)


def observe(domain):
    with self_destruct_enemy_ammo(domain[0]['enemy_ammo']) as ammo:n=self_observe(domain,include_ammo=True)
    n['enemy_ammo']=ammo
    return n
