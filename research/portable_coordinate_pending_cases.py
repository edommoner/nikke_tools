"""Literal legacy B3 contracts: a body packet, never a coordinate expansion."""
import copy
from portable_coordinate_area_cases import fixtures as area_cases
from world_pending_cases import fixtures as pending_cases
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant


def fixtures():
    base=copy.deepcopy(area_cases()[0]);pending=pending_cases()[0];rows=[]
    base['duration']=1
    base['effects']=[*base['effects'][:2],copy.deepcopy(pending['effects'][0]),dict(pending['effects'][1],name='parts-source')]
    base['owners']=[0]*4;base['observe_pending_skills']=True
    base['observe_authored_effect_lookup']=True
    for i,weapon in enumerate(base['combat']['weapons']):
        weapon.update(stage=pending['combat']['weapons'][i]['stage'],cooldown=40)
    def add(label,damage=750):
        case=copy.deepcopy(base);case['name']='coordinate-pending/'+label
        case['contract']=dict(event_kinds=['packet'] if damage else [],packets=[('',damage)] if damage else [],
            selected=[],geometry=[],damage=[damage,0,0,0,0],interrupt=[0]*5,notices=0,marker=False)
        rows.append(case);return case
    add('legacy-body')
    case=add('zero',0);case['effects'][-1]['fixed_value']=0
    case=add('earlier-cast-buff',1500);case['effects'].insert(-1,field('atk_pct',100,'self','earlier','burst_cast'));case['owners'].insert(-1,0)
    case=add('later-cast-buff');case['effects'].append(field('atk_pct',100,'self','later','burst_cast'));case['owners'].append(0)
    case=add('fullburst-entry-buff',1500);case['effects'].append(field('atk_pct',100,'self','entry','full_burst_start'));case['owners'].append(0)
    case=add('parts-born-before-landing');case['patterns'][0]['delay']=.55
    case=add('parts-expired-before-landing');case['patterns'][0]['until']=dict(time=.3)
    case=add('lifesteal-body-only');case['effects'].insert(0,instant('current_hp_reduce',50,'self','drain'));case['owners'].insert(0,0)
    case['effects'].insert(-1,field('lifesteal_pct',10,'self','leech'));case['owners'].insert(-1,0)
    case['contract']['hp']=[5075,10000,10000,10000,10000]
    return rows
