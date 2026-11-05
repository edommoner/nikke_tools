"""Original physical focus cases plus explicit lifesteal and scatter consumers."""
import copy
from portable_focus_aim_cases import original_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field


def fixtures():
    rows=original_fixtures()
    for case in rows:case['name']='interrupt-aim-'+case['name'].removeprefix('focus-aim-')
    for label,dead,scatter in [('lifesteal',False,False),('dead-scatter-lifesteal',True,True)]:
        case=copy.deepcopy(rows[0]);case['name']='interrupt-aim-'+label
        case['effects'] += [instant('current_hp_reduce',50,'all_allies','drain'),field('lifesteal_pct',10,'all_allies','lifesteal')]
        case['owners'] += [0,0]
        if dead:case['patterns'][0]['targets'][0]['hp']=1
        if scatter:
            for weapon in case['combat']['weapons'][:2]:weapon.update(pellets=3,muzzles=2,base_weapon_type='SG')
        rows.append(case)
    case=copy.deepcopy(rows[0]);case['name']='interrupt-aim-repeat-generation'
    case['patterns'][0].update(after=['start','stop'],repeat=2,until=dict(targets_cleared=True))
    case['patterns'][0]['targets'][0]['hp']=1
    rows.append(case)
    for label,healing in [('charge',False),('charge-lifesteal',True)]:
        case=copy.deepcopy(next(c for c in rows if c['name']=='interrupt-aim-lifesteal') if healing else rows[0])
        case['name']='interrupt-aim-'+label
        case['weapon_metadata']['fire_stance_hold']=0
        for weapon in case['combat']['weapons'][:2]:weapon.update(mode='charge',charge=.05,interval=.1,min_cycle=.1,full_charge_mult=100,base_weapon_type='SR')
        rows.append(case)
    case=copy.deepcopy(rows[0]);case['name']='interrupt-aim-gated-vanish'
    case['patterns'].append(dict(id='hidden',kind='vanish',until=dict(time=1)))
    rows.append(case)
    return rows
