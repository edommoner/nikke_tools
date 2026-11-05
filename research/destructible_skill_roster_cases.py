"""Full original Rei skills, literal shield windows and original selectors."""
import importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('skill_shield_rei_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    rows=[]
    for label,duration,start,kind,capacity in [('early-hp',3,.5,3,1e12),('hp',30,4.,3,1e12),('hit',30,4.,4,50.),('break',30,4.,3,500.)]:
        body=dict(m.body_for(m.policy.roster_for('레이'),duration),burst_gauge_mode='accumulate')
        body['enemy']['patterns']=[dict(id='declared-shield',kind='idle',delay=start,until=dict(time=.3)),dict(id='incoming-damage',kind='attack',delay=.1,spec=dict(atk=300000,coeff=100,target='all',pierce=True))]
        rows.append(dict(name='destructible-skill-roster/Rei/'+label,body=body,typed_bindings=[dict(node='declared-shield',kind=kind,identity=10,capacity=capacity,owner=[0,0,1])],max_attacks=128,skill_shield_interception_v1=True,contract=dict(profile='레이',label=label,duration=duration,original_skill_definitions=7,prepared_definitions=73)))
    return rows
