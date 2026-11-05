"""Complete Mana roster: original ally-down revival and one-use state removal."""
import importlib.util
from pathlib import Path

def fixtures():
    spec=importlib.util.spec_from_file_location('original_revival_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)
    rows=[]
    for label,hits in [('control',0),('once',1),('twice',2)]:
        patterns=[dict(id='world',kind='idle')]
        if hits:patterns.append(dict(id='kill',kind='attack',delay=1.,spec=dict(atk=1e8,coeff=100,target='slot:4',pierce=True,hits=hits,interval=.5)))
        rows.append(dict(name='coordinate-original-revival/Mana/'+label,body=dict(factory.body_for(factory.policy.roster_for('마나'),3),burst_gauge_mode='accumulate',seed=2601),coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=patterns,expected_downs=hits))
    return rows
