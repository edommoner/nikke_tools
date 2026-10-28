"""Original full battle under declared named radial candidate filtering."""
from named_range_battle import named_range_battle
from world_logical_geometry_native import observe as full_original

def observe(case):
    with named_range_battle(case['named_range_rules'],case['logical_geometry']) as selection:
        native,trace=full_original(case)
    native['named_range_battle']=selection
    return native,trace
