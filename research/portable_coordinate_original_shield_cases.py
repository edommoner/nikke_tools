"""Complete original shield-heal definitions with declared real incoming hits."""
import importlib.util
from pathlib import Path

def fixtures():
    spec=importlib.util.spec_from_file_location('original_shield_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
    rows=[]
    for name,label in [('라푼젤 : 퓨어 그레이스','Rapunzel-pure-grace'),('모리','Mori'),('킬로','Kilo')]:
        for scenario,attack in [('full',0),('chipped',400000),('broken',2000000)]:
            body=dict(f.body_for(f.policy.roster_for(name),6),burst_gauge_mode='accumulate',seed=3401)
            if label=='Rapunzel-pure-grace':body['shooting_policy']='character'
            patterns=[dict(id='world',kind='idle')]
            if scenario=='chipped' and label=='Mori':attack=800000
            if attack:patterns.append(dict(id='original-shield-hit',kind='attack',delay=4. if scenario=='broken' else 1.,spec=dict(atk=attack,coeff=100,target='slot:1',pierce=True,hits=1,interval=.1)))
            if scenario=='chipped':
                check=3.2 if label=='Rapunzel-pure-grace' else 5.5 if label=='Mori' else 5.95
                patterns.append(dict(id='original-shield-check',kind='attack',delay=check,spec=dict(atk=2000000,coeff=100,target='slot:1',pierce=True,hits=1,interval=.1)))
            rows.append(dict(name='coordinate-original-shield/'+label+'/'+scenario,body=body,coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=patterns,shield_witness=dict(character=label,scenario=scenario)))
    return rows
