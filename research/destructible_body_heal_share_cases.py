"""Complete Rem/Milk and two RL recipients, with/without real Trony pools."""
import importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('body_share_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
    rows=[]
    for last,label in [('누아르','Noir'),('트로니','Trony')]:
        for duration in (3,30):
            for mode,kind,capacity in [('hp',3,1e12),('hit',4,128.),('break',3,100.)]:
                body=dict(r.body_for(['밀크','렘','아니스','N102',last],duration),burst_gauge_mode='accumulate')
                body['enemy']['patterns']=[dict(id='incoming',kind='attack',delay=.1,spec=dict(atk=300000,coeff=100,target='all',pierce=True)),dict(id='shield',kind='idle',delay=2.8,until=dict(time=.4))]
                rows.append(dict(name=f'destructible-body-heal-share/{label}/{duration}s/{mode}',body=body,typed_bindings=[dict(node='shield',kind=kind,identity=10,capacity=capacity,owner=[0,0,1])],max_attacks=128,skill_shield_interception_v1=True,body_lifesteal_v1=True,body_accumulation_v1=True,body_heal_sharing_v1=True,contract=dict(label=label,duration=duration,mode=mode)))
    return rows
