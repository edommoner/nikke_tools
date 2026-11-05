"""Original gauges and resource-dependent callbacks, with complete real rosters."""
import importlib.util
from pathlib import Path

def fixtures():
    spec=importlib.util.spec_from_file_location('original_resource_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
    rows=[]
    for name,label,duration,adds in [('E.H.','EH-start',3,0),('E.H.','EH-cap',3,24),('네온 : 비전 아이','Neon-burst',6,0)]:
        patterns=[dict(id='world',kind='idle')]
        if adds:patterns.append(dict(id='resource-adds',kind='summon',delay=.5,spec=dict(count=adds,hp=1)))
        rows.append(dict(name='coordinate-original-resources/'+label,body=dict(f.body_for(f.policy.roster_for(name),duration),burst_gauge_mode='accumulate',seed=2801),coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=patterns,resource_witness=label))
    return rows
