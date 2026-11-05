"""Canonical enemy effect scope stays body while physical aim targets interrupts."""
import copy
from portable_aimed_area_cases import fixtures as areas
from portable_interrupt_aim_cases import fixtures as direct
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant


def fixtures():
    rows=[]
    for label,seed in [('direct',direct()[0]),('pierce',areas()[0]),('explosion',areas()[3]),('part',direct()[17])]:
        case=copy.deepcopy(seed);case['name']='aimed-enemy-'+label
        case['observe_parts_accounting']=True
        old=field('received_dmg_pct',50,'boss','scope-marker')
        child=field('received_dmg_pct',25,'target','conditional-replacement',timing='hit_count:2',condition=['target_state:scope-marker'])
        removal=instant('remove_named_buff',0,'target','scope-remove',timing='hit_count:2');removal['target_effect']='scope-marker';removal['trigger']['condition']=['target_state:scope-marker']
        case['effects'] += [old,child,removal];case['owners'] += [0,0,0];rows.append(case)
    for condition in ('target_is_boss','target_is_add'):
        case=copy.deepcopy(direct()[0]);case['name']='aimed-enemy-'+condition
        case['observe_parts_accounting']=True
        case['effects'].append(field('atk_pct',100,'self','logical-witness',timing='hit_count:2',condition=[condition]));case['owners'].append(0);rows.append(case)
    return rows
