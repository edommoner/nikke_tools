"""Complete original ammo effects, including gauge steps and signed removal."""
import importlib.util
from pathlib import Path

def fixtures():
    spec=importlib.util.spec_from_file_location('original_ammo_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
    rows=[]
    for name,label,duration in [('길로틴 : 윈터 슬레이어','Guillotine-winter',6),('누아르','Noir',6),('아르카나 : 포츈 메이트','Arcana',6),('그레이브','Grave-drain',16)]:
        rows.append(dict(name='coordinate-original-ammo/'+label,body=dict(f.body_for(f.policy.roster_for(name),duration),burst_gauge_mode='accumulate',seed=2901),coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=[dict(id='world',kind='idle')],ammo_witness=label))
    return rows
