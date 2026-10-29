"""Full unchanged original comparison chain with the declared movement reader."""
import copy
from enemy_movement_model import enemy_movement
from portable_enemy_movement_wire import compile_battle
from portable_coordinate_original_cases import prepare_case as original_case
from world_logical_geometry_full_native import observe as original_observe

def prepare_case(row):
    case,prepared=original_case(row)
    case.update(logical_geometry=copy.deepcopy(row['logical_geometry']),enemy_movement=copy.deepcopy(row['enemy_movement']),
        logical_geometry_contract=copy.deepcopy(row['contract']),enemy_movement_contract=copy.deepcopy(row['contract']),sampled_groups=True)
    words,meta,bindings,scene=compile_battle(prepared,case['logical_geometry'],case['enemy_movement'])
    return words,(case,meta,bindings,scene)

def observe(domain):
    with enemy_movement(domain[0]['enemy_movement']) as motion:native=original_observe(domain)
    native['enemy_movement']=motion
    return native
