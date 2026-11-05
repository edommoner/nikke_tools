"""Complete Rei definitions and literal incoming hits, no CPU activation schedule."""
import importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('original_decoy_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);rows=[]
    for scenario in ('full','chipped','broken'):
        patterns=[dict(id='world',kind='idle')]
        if scenario!='full':patterns.append(dict(id='decoy-hit',kind='attack',delay=1. if scenario=='chipped' else 4.,spec=dict(atk=400000 if scenario=='chipped' else 5000000,coeff=100,target='slot:1',ignore_taunt=True,hits=1,interval=.1)))
        if scenario=='chipped':patterns.append(dict(id='decoy-check',kind='attack',delay=5.5,spec=dict(atk=2000000,coeff=100,target='slot:1',ignore_taunt=True,hits=1,interval=.1)))
        rows.append(dict(name='coordinate-original-decoy/Rei/'+scenario,body=dict(f.body_for(f.policy.roster_for('라이'),8),burst_gauge_mode='accumulate',seed=3601),coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=patterns,decoy_witness=scenario))
    return rows
