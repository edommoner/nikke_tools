"""Same original full battle and enemy magazine contract; no profile edits."""
import copy
from enemy_ammo_model import enemy_ammo
from portable_enemy_ammo_wire import compile_enemy_ammo
from portable_coordinate_original_cases import prepare_case as original_case
from world_add_attack_battle_native import observe as incoming_battle


def prepare_case(row):
    case,prepared=original_case(row)
    case.update(logical_geometry=copy.deepcopy(row['logical_geometry']),enemy_ammo=copy.deepcopy(row['enemy_ammo']),enemy_ammo_contract=copy.deepcopy(row['contract']),sampled_groups=True)
    words,meta,bindings,scene=compile_enemy_ammo(prepared,case['logical_geometry'],case['enemy_ammo'])
    return words,(case,meta,bindings,scene)


def observe(domain):
    from world_original_resource_native import capture
    with capture(domain[0],include_ammo=True) as resources,enemy_ammo(domain[0]['enemy_ammo']) as ammo:n=incoming_battle(domain)
    n['enemy_ammo']=ammo
    n['original_resources']=resources
    return n
