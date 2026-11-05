"""Unedited original stacks: increase, cap, consumption and later recharge."""
import importlib.util
from pathlib import Path

def fixtures():
    spec=importlib.util.spec_from_file_location('original_stack_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
    rows=[]
    for name,label,duration,adds in [('페퍼','Pepper-no-carrier',6,0),('루피','Rupee',10,0),('마르차나 : 마린 스터디','Marine-cap',6,0),('마르차나 : 마린 스터디','Marine-consume-recharge',6,6)]:
        patterns=[dict(id='world',kind='idle')]
        if adds:patterns.append(dict(id='stack-adds',kind='summon',delay=.5,until=dict(time=3),spec=dict(count=adds,hp=1e12)))
        rows.append(dict(name='coordinate-original-stacks/'+label,body=dict(f.body_for(f.policy.roster_for(name),duration),burst_gauge_mode='accumulate',seed=3001),coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=patterns,stack_witness=label))
    return rows
