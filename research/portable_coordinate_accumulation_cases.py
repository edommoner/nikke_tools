"""Literal witnesses distinguishing native exclusions from GPU port gaps."""
import copy
from portable_coordinate_physical_common_cases import fixtures as physical
from world_enemy_attack_cases import field


def fixtures():
    source=physical();rows=[]
    for label,index,current in [('target-only',1,0),('body-and-parts',6,2000),('body-parts-interrupt',6,2000)]:
        case=copy.deepcopy(source[index]);case['name']='coordinate-accumulation-policy/'+label
        case['effects'].append(field('dmg_accum_dealt_atk_pct',1000,'target','coordinate-pool','battle_start',.4));case['owners'].append(0)
        case['expected_accumulation']=current
        if label=='body-parts-interrupt':case['patterns'].insert(0,dict(id='interrupt',kind='interrupt',targets=[dict(name='stop',hp=1e8,x=0,y=0,r=2,z=3)]))
        rows.append(case)
    return rows
