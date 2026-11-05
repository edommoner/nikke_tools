"""Existing full original owner battle, with an explicit cover layer model."""
from cover_defense_battle_model import cover_defense
from portable_original_catalogue_cases import prepare
from world_coordinate_typed_owner_native import observe as original

def observe(case):
    c,_=prepare(case)
    with cover_defense(case['cover_defense'],case['contract']['names']) as data:native,trace=original(c)
    native['cover_defense']=data
    return native,trace
