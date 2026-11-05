"""Literal180-second bodies; no authored hit lists or truncation policies."""
import copy
from portable_battle_native_route_cases import fixtures as native_cases
from portable_battle_attack_group_cases import fixtures as scene_cases

def fixtures():
    seeds=[c for c in native_cases() if c['contract']['duration']==3 and c['contract']['adds']==3 and c['contract'].get('baseline_unchanged')]
    seeds+=[c for c in scene_cases() if c['contract']['duration']==3 and c['contract']['adds']==5 and c['contract']['capacity']!=1.]
    seeds+=[c for c in native_cases() if c['contract'].get('declared_listener') and not c['contract'].get('reselection')]
    rows=[]
    for original in seeds:
        c=copy.deepcopy(original);c['body']['duration']=180;c['contract']['duration']=180;c['group_history']='compact'
        c['name']='attack-group-long/'+c['routing']+'/'+c['contract']['profile']
        rows.append(c)
    assert len(rows)==6 and len({c['name'] for c in rows})==6
    return rows
