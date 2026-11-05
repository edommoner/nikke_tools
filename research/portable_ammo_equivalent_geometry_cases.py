"""Geometry predicates under actor-pool admission, including true/false paths."""
import copy
from portable_ammo_equivalent_cases import fixtures as base_fixtures
from world_enemy_attack_cases import field

def fixtures():
    rows=[]
    for label,condition,damage in [('core-present','core_hit',(6000,7200,8400)),('core-below-one','core_hit',(6000,6600,7200)),('range-present','optimal_range',(7800,9360,10920)),('range-absent','optimal_range',(6000,6600,7200))]:
        case=copy.deepcopy(base_fixtures()[0]);case['name']='ammo-equivalent-geometry-'+label
        case['weapon_metadata']['core_dmg_mult']=100
        for weapon in case['combat']['weapons']:weapon['core_mult']=100
        if label.startswith('core'):case['enemy']['core_px']=1 if label=='core-present' else .5
        else:case['enemy']['optimal_range_weapons']=['AR'] if label=='range-present' else []
        case['effects'].append(field('atk_pct',10,'self','geometry-watch','on_attack',condition=[condition],max_stack=128));case['owners'].append(0)
        case['contract']['packet_damage']=list(damage);rows.append(case)
    return rows
