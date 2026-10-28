"""Complete old observers plus the original named radial battle scope."""
import copy
from named_range_battle import named_range_battle
from portable_named_range_battle_wire import compile_battle
from portable_coordinate_original_cases import prepare_case as original_case
from world_logical_geometry_full_native import observe as full_original

def prepare_case(row):
    case,prepared=original_case(row)
    case.update(logical_geometry=copy.deepcopy(row['logical_geometry']),named_range_rules=copy.deepcopy(row['named_range_rules']),named_range_contract=copy.deepcopy(row['contract']),sampled_groups=True)
    w,m,b,s=compile_battle(prepared,case['logical_geometry'],case['named_range_rules'])
    return w,(case,m,b,s)
def observe(domain):
    with named_range_battle(domain[0]['named_range_rules'],domain[0]['logical_geometry']) as data:n=full_original(domain)
    n['named_range_battle']=data
    return n
