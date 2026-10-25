"""Original Mihara target DoT stacks, actual shots and literal lethal input."""
import importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('original_enemy_stack_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
    rows=[];name='미하라 : 본딩 체인'
    for label,names,duration in [('control',f.policy.roster_for(name),4),('hits',['드레이크','미란다','도라',name,'메어리'],11),('down',f.policy.roster_for(name),4),('transfer',f.policy.roster_for(name),8)]:
        patterns=[dict(id='world',kind='idle')]
        if label=='down':patterns.append(dict(id='lethal',kind='attack',delay=1.,spec=dict(atk=1e8,coeff=100,target='slot:1',ignore_taunt=True,pierce=True)))
        rows.append(dict(name='coordinate-original-enemy-stack/Mihara/'+label,body=dict(f.body_for(names,duration),burst_gauge_mode='accumulate',seed=3801),coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=patterns,enemy_stack_witness=label))
    return rows
