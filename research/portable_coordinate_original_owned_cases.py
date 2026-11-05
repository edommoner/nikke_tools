"""Complete Ein/Cinderella profiles with public default/weapon-swap policies."""
import importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('original_owned_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
    rows=[]
    for name,label,durations in [('아인','Ein',(1,12,40)),('신데렐라 : 크리스탈 웨이브','Cinderella-Crystal',(3,30))]:
        for duration in durations:
            body=dict(f.body_for(f.policy.roster_for(name),duration),burst_gauge_mode='accumulate',seed=4101)
            if label.startswith('Cinderella'):body['weapon_mode_swap']=True
            rows.append(dict(name='coordinate-original-owned/'+label+'/'+str(duration)+'s',body=body,coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=[dict(id='world',kind='idle')],owned_witness=label))
    return rows
