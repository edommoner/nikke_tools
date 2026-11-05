"""Original cleansers with real permanent allied demerits and enemy overlays."""
import importlib.util
from pathlib import Path

def fixtures():
    spec=importlib.util.spec_from_file_location('original_cleanse_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
    rows=[]
    for label,names,duration in [('Cocoa-empty',f.policy.roster_for('코코아'),6),('Cocoa-partial',['코코아','도라','베스티','N102','메어리'],16),('Mica-all',['미카 : 스노우 버디','도라','베스티','드레이크','메어리'],26),('Rosanna-overlays',f.policy.roster_for('로산나'),3)]:
        patterns=[dict(id='world',kind='idle')]
        if label=='Rosanna-overlays':patterns.extend([dict(id='ordinary-a',kind='buff',enemy=dict(def_mult=2,received_dmg_pct=-25)),dict(id='fixed',kind='buff',irremovable=True,enemy=dict(def_add=50,received_dmg_pct=-10)),dict(id='ordinary-b',kind='buff',delay=.1,enemy=dict(def_mult=3,received_dmg_pct=-10))])
        rows.append(dict(name='coordinate-original-cleanse/'+label,body=dict(f.body_for(names,duration),burst_gauge_mode='accumulate',seed=3101),coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=patterns,cleanse_witness=label))
    return rows
