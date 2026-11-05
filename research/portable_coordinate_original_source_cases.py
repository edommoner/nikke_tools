"""Complete original forced skills and real part-destruction duration changes."""
import importlib.util
from pathlib import Path

def fixtures():
    spec=importlib.util.spec_from_file_location('original_source_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
    rows=[]
    for name,stage,label,parts,duration in [('율리아',1,'Julia-1',False,3),('율리아',2,'Julia-2',False,3),('율리아',3,'Julia-3',False,3),('사쿠라 : 블룸 인 서머',0,'Sakura-control',False,18),('사쿠라 : 블룸 인 서머',0,'Sakura-parts',True,18)]:
        body=dict(f.body_for(f.policy.roster_for(name),duration),burst_gauge_mode='accumulate',seed=3201);body['profile']['chars'][name]['favorite_stage']=stage
        if stage:body['profile']['chars'][name]['collection_stage']='SR15'
        patterns=[dict(id='world',kind='idle')]
        if parts:patterns.append(dict(id='original-parts',kind='parts',delay=.5,targets=[dict(name='original-breakable',hp=1,x=0,y=0,r=10,z=1,emit_on_destroy=['event:part_destroy'])]))
        rows.append(dict(name='coordinate-original-source/'+label,body=body,coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=patterns,source_witness=label))
    return rows
