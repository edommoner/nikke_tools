"""Original normal shots and native per-pellet target reselection, no hit lists."""
import copy
from portable_battle_attack_group_cases import fixtures as originals

def fixtures():
    rows=[]
    for source in originals():
        if source['contract'].get('reopened') or source['contract']['capacity']==1.:continue
        case=copy.deepcopy(source);case['routing']='native'
        case['name']=case['name'].replace('attack-group-battle/','attack-group-native-route/')
        case['contract']['native_route']=True
        case['contract']['baseline_unchanged']=not case['contract'].get('declared_listener')
        rows.append(case)
        if case['contract'].get('declared_listener'):
            broken=copy.deepcopy(case);broken['name']+='/pellet-reselection'
            broken['body']['enemy']['patterns'][0]['spec'].update(count=3,hp=1.)
            broken['contract'].update(adds=3,capacity=1.,reselection=True)
            rows.append(broken)
    return rows
