"""Original Milk allied lifesteal with real shot/skill shield interception."""
import importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('body_lifesteal_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
    rows=[]
    for duration in (3,30):
        for label,kind,capacity,length,owner in [('hp',3,1e12,.4,1),('hit',4,128.,.4,1),('break',3,100.,.4,1),('expiry',3,1e12,.05,1),('stale-owner',3,1e12,.4,2)]:
            body=dict(r.body_for(['누아르','밀크','도라','레이','미사토'],duration),burst_gauge_mode='accumulate')
            body['enemy']['patterns']=[dict(id='incoming',kind='attack',delay=.1,spec=dict(atk=300000,coeff=100,target='all',pierce=True)),dict(id='shield',kind='idle',delay=2.8,until=dict(time=length))]
            rows.append(dict(name=f'destructible-body-lifesteal/{duration}s/{label}',body=body,typed_bindings=[dict(node='shield',kind=kind,identity=10,capacity=capacity,owner=[0,0,owner])],max_attacks=128,skill_shield_interception_v1=True,body_lifesteal_v1=True,contract=dict(duration=duration,label=label)))
    return rows
