"""All eight original area contracts plus mixed reached pools; no case shrinking."""
import copy
from portable_aimed_packet_cases import fixtures as packet_fixtures
from world_enemy_attack_cases import field


def fixtures():
    rows=packet_fixtures()[8:]
    for label,index,wide in [('mixed-pierce',0,False),('mixed-explosion',3,False),('mixed-wide-pierce',0,True),('mixed-wide-explosion',3,True)]:
        case=copy.deepcopy(rows[index]);case['name']='aimed-area-'+label
        case['patterns'][0]['targets'].append(dict(name='other-stop',hp=1e8,reach=1))
        case['patterns'].append(dict(id='parts-nearby',kind='parts',targets=[dict(name='near-part',hp=1e8,reach=1),dict(name='far-part',hp=1e8,reach=4)]))
        case['effects'].append(field('part_dmg_pct',25,'all_allies','nearby-part-factor'));case['owners'].append(0)
        if wide:
            case['effects'].append(field('explosion_range' if index==3 else 'pierce_range',100,'all_allies','wide'));case['owners'].append(0)
        rows.append(case)
    for case in rows:case['observe_parts_accounting']=True
    return rows
