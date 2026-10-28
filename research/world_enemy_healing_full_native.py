"""Complete original battle observation with one declared enemy heal scope."""
import copy
from enemy_healing_model import enemy_healing
from portable_enemy_healing_wire import compile_enemy_healing
from portable_coordinate_original_cases import prepare_case as original_case
from world_logical_geometry_full_native import observe as logical_battle


def prepare_case(row):
    case, prepared = original_case(row)
    case.update(logical_geometry=copy.deepcopy(row['logical_geometry']),
                enemy_healing=copy.deepcopy(row['enemy_healing']),
                enemy_healing_contract=copy.deepcopy(row['contract']))
    words, meta, bindings, scene = compile_enemy_healing(prepared, case['logical_geometry'], case['enemy_healing'])
    return words, (case, meta, bindings, scene)


def observe(domain):
    with enemy_healing(domain[0]['enemy_healing']) as healing:
        native = logical_battle(domain)
    native['enemy_healing'] = healing
    return native
