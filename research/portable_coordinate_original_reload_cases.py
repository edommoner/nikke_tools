"""Original reload definitions with declared public controls, no effect edits."""
import importlib.util
from pathlib import Path

def fixtures():
    spec=importlib.util.spec_from_file_location('original_reload_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
    rows=[]
    for name,label,duration,hold in [('밀크 : 블루밍 바니','Milk-auto',18,False),('밀크 : 블루밍 바니','Milk-character',18,True),('아스카 : WILLE','Asuka-WILLE',15,False),('질','Jill',6,False)]:
        body=dict(f.body_for(f.policy.roster_for(name),duration),burst_gauge_mode='accumulate',seed=3301)
        if hold:
            body['shooting_policy']='character'
        rows.append(dict(name='coordinate-original-reload/'+label,body=body,coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=[dict(id='world',kind='idle')],reload_witness=label))
    return rows
