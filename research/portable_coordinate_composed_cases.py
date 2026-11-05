"""Shared body-shot groups and coordinate skill packets on the same frame."""
import copy
from portable_coordinate_skill_cases import fixtures as coordinate_cases
from world_enemy_attack_cases import field


def fixtures():
    rows=[]
    for owner,pellets,muzzles in [(0,1,1),(0,3,1),(0,3,2),(3,1,1),(3,3,1),(3,3,2)]:
        case=copy.deepcopy(coordinate_cases()[2]);case.pop('contract')
        case.update(name=f'coordinate-composed/body-groups/{owner}/{pellets}/{muzzles}',duration=.35,
                    patterns=[dict(id='idle',kind='idle')],coordinate_packet_trace=True,
                    group_owner=owner)
        case['combat']['weapons'][owner]=dict(enabled=True,stage=0,gauge=0,capacity=30,
            interval=.1,reload=.4,pellets=pellets,muzzles=muzzles,mode='auto')
        case['effects'][-1]['trigger']['timing']=['battle_start','every:0.1s']
        case['effects'].append(field('atk_pct',0,'self','composed-group-notification',timing='multi_hit:1'));case['owners'].append(owner)
        if owner!=0:
            case['effects'].append(field('crit_rate',-100,'self','group-no-crit'));case['owners'].append(owner)
        rows.append(case)
    return rows
