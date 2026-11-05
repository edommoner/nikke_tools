"""Original accumulator lifetimes on real coordinate physical battle geometry."""
import copy
from portable_damage_accum_cases import fixtures as accumulation
from portable_coordinate_physical_gpu_cases import fixtures as physical
from world_enemy_attack_cases import field


def fixtures():
    geometry=physical()[7];rows=[]
    for original in accumulation():
        # ADD sharing and attack nodes are outside the coordinate scene schema.
        # Retain their original suites; do not claim coordinate coverage for them.
        if original['contract']['kind'] in ('add-share-excluded','explicit-boss-share','down-keeps-name-archive'):continue
        case=copy.deepcopy(original);case.pop('contract')
        case['name']='coordinate-accum-emission/'+original['name'].removeprefix('damage-accum-')
        case['enemy']['coord']=copy.deepcopy(geometry['enemy']['coord'])
        case['weapon_metadata']=copy.deepcopy(geometry['weapon_metadata'])
        case['patterns']=copy.deepcopy(geometry['patterns'])+case['patterns']
        case['effects'].append(field('pierce_enabled',1,'all_allies','coordinate-physical-pierce'))
        case['owners'].append(0);case['observe_coordinate_landings']=True;rows.append(case)
    first=copy.deepcopy(rows[0])
    for label in ['fully-occluded','interrupt','destroyed-parts','two-coordinate-shooters']:
        case=copy.deepcopy(first);case['name']='coordinate-accum-emission/'+label
        if label=='fully-occluded':
            case['effects']=[e for e in case['effects'] if e.get('stat')!='pierce_enabled'];case['owners']=case['owners'][:-1]
            case['patterns'][0]['targets'][0]['r']=100
        elif label=='interrupt':case['patterns'].insert(0,dict(id='interrupt',kind='interrupt',targets=[dict(name='stop',hp=1e8,x=0,y=0,r=3,z=3)]))
        elif label=='destroyed-parts':
            for target in case['patterns'][0]['targets']:target['hp']=1
        else:case['combat']['weapons'][3]=copy.deepcopy(case['combat']['weapons'][0])
        rows.append(case)
    return rows
