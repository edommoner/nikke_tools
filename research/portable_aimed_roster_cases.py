"""Unfiltered existing real profiles in literal interrupt and penalty-part worlds."""
import copy
from portable_state_focus_roster_cases import fixtures as originals


def fixtures():
    rows=[]
    for original in originals():
        for world in ('interrupt','part'):
            case=copy.deepcopy(original);case['name']=original['name'].replace('state-focus-real/','aimed-real/')+'/'+world
            case['aim_policy']=dict(aim_interrupt=True,camera=[case['character']],camera_mode='single')
            if world=='interrupt':
                patterns=[dict(id='stop',kind='interrupt',targets=[dict(name='stop',hp=1e30,reach=1)]),dict(id='parts-near',kind='parts',targets=[dict(name='nearby',hp=1e30,reach=1)])]
            else:
                patterns=[dict(id='parts',kind='parts',until=dict(targets_cleared=True,time=case['duration']+1),targets=[dict(name='penalty',hp=1e30,reach=1)]),dict(id='failure',kind='idle',after=[dict(node='parts',outcome='expired')])]
            case['body']['enemy']['patterns']=patterns
            rows.append(case)
    return rows
