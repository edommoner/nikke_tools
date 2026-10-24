"""Unmodified Misato roster effects and weapons, early/late declared shields."""
import importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('weapon_shield_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    rows=[]
    for duration,start in [(3,.5),(30,4.)]:
        body=dict(m.body_for(m.policy.roster_for('미사토'),duration),burst_gauge_mode='accumulate')
        body['enemy']['patterns']=[dict(id='declared-weapon-shield',kind='idle',delay=start,until=dict(time=.1)),dict(id='declared-incoming-damage',kind='attack',delay=.1,spec=dict(atk=300000,coeff=100,target='all',pierce=True))]
        rows.append(dict(name='destructible-weapon-roster/Misato/'+str(duration)+'s',body=body,typed_bindings=[dict(node='declared-weapon-shield',kind=3,identity=10,capacity=1e12,owner=[0,0,1])],max_attacks=128,contract=dict(duration=duration,profile='미사토',own_effects=5,all_effects=71,modifier_active=duration==30)))
    return rows
