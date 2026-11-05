"""Original Soda skill levels, no effect edits or precomputed activation schedule."""
import importlib.util
from pathlib import Path

def fixtures():
    spec=importlib.util.spec_from_file_location('original_init_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
    rows=[];name='소다 : 트윙클링 바니'
    for level in (1,4,10):
        body=dict(f.body_for(f.policy.roster_for(name),8),burst_gauge_mode='accumulate',seed=3701)
        body['profile']['chars'][name]['skill_levels']['1']=level
        rows.append(dict(name='coordinate-original-init/Soda/level-'+str(level),body=body,coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=[dict(id='world',kind='idle')],init_level=level))
    return rows
