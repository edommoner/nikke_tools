"""Original Noir/Misato/Rei definitions; direct AoE and live shield mixtures."""
import copy
import importlib.util
from pathlib import Path


def fixtures():
    spec=importlib.util.spec_from_file_location('aoe_shield_roster_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'))
    roster=importlib.util.module_from_spec(spec);spec.loader.exec_module(roster)
    rows=[]
    for duration in (3,30):
        for label,shields in (
            ('hp',[(3,1e12)]),('hit',[(4,64.)]),
            ('hit-then-hp',[(4,1.),(3,1e12)]),
            ('hp-then-hit',[(3,500.),(4,64.)]),
            ('break-body',[(3,500.)]),('stale-owner',[(3,1e12)])):
            body=dict(roster.body_for(['누아르','미란다','도라','레이','미사토'],duration),burst_gauge_mode='accumulate')
            body['enemy']['patterns']=[dict(id='declared-shield',kind='idle',delay=2.8,until=dict(time=.4)),dict(id='incoming-damage',kind='attack',delay=.1,spec=dict(atk=300000,coeff=100,target='all',pierce=True))]
            bindings=[dict(node='declared-shield',kind=kind,identity=10+i,capacity=capacity,owner=[0,0,2 if label=='stale-owner' else 1]) for i,(kind,capacity) in enumerate(shields)]
            rows.append(dict(name=f'destructible-aoe-burst-roster/{duration}s/{label}',body=body,typed_bindings=bindings,max_attacks=128,skill_shield_interception_v1=True,
                             contract=dict(label=label,duration=duration,prepared_definitions=78,own_definitions={'누아르':8,'미란다':5,'도라':8,'레이':7,'미사토':5})))
    for duration in (3,30):
        for label,kind,capacity in [('hp',3,1e12),('hit',4,64.)]:
            case=copy.deepcopy(next(c for c in rows if c['contract']['duration']==duration and c['contract']['label']==label))
            case['name']=f'destructible-aoe-burst-roster/{duration}s/trina-{label}'
            case['body']=dict(roster.body_for(['누아르','미란다','트리나','레이','미사토'],duration),burst_gauge_mode='accumulate',enemy=copy.deepcopy(case['body']['enemy']))
            case['contract'].update(prepared_definitions=83,aoe_specific_bonus=435.6)
            del case['contract']['own_definitions']['도라'];case['contract']['own_definitions']['트리나']=13
            rows.append(case)
    return rows
