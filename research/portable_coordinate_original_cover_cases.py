"""Original cover revival: actual reload cover, literal boss hits, original bursts."""
import importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('original_cover_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
    rows=[]
    for name,label in [('비스킷','Biscuit'),('릴리','Lili')]:
        for scenario in ('full','singleton','pool'):
            patterns=[dict(id='world',kind='idle')]
            hits=[] if scenario=='full' else [(2,11.6)]
            if scenario=='pool':hits += [(3,14.2),(5,14.2)] if label=='Biscuit' else [(1,11.6),(3,14.2)]
            for slot,when in hits:patterns.append(dict(id='break-cover-'+str(slot),kind='attack',delay=when,spec=dict(atk=2500000,coeff=100,target='slot:'+str(slot),ignore_taunt=True,hits=1,interval=.1)))
            body=dict(f.body_for(f.policy.roster_for(name),6 if scenario=='full' else 46),burst_gauge_mode='accumulate',seed=3501)
            rows.append(dict(name='coordinate-original-cover/'+label+'/'+scenario,body=body,coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=patterns,cover_witness=dict(character=label,scenario=scenario,broken=len(hits),revived=0 if scenario=='full' else min(2 if label=='Biscuit' else 1,len(hits)))))
    return rows
