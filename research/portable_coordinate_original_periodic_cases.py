"""Complete same-label periodic sources, with original definitions and metadata."""
import importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('original_periodic_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
    rows=[]
    for name,label in [('하란','Harran'),('쿠루미','Kurumi')]:
        for duration in (3,30):
            body=dict(f.body_for([name,'미란다','도라','N102','메어리'],duration),burst_gauge_mode='accumulate',seed=2501)
            rows.append(dict(name=f'coordinate-original-periodic/{label}/{duration}s',body=body,coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=[dict(id='world',kind='idle')]))
    return rows
