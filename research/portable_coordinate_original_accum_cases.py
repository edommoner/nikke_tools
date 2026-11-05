"""Original expiry/full accumulator releases; no effect or firing schedule edits."""
import importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('original_accum_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
    rows=[]
    for character,label in [('도로시','Dorothy'),('트로니','Trony')]:
        for witness,duration in [('control',1),('release',18)]:
            rows.append(dict(name='coordinate-original-accum/'+label+'/'+witness,body=dict(f.body_for(f.policy.roster_for(character),duration),burst_gauge_mode='accumulate',seed=4001),coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=[dict(id='world',kind='idle')],accum_witness=witness))
    return rows
