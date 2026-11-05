"""Complete original Emilia definitions; no effect or timing rewrites."""
import importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('max_ammo_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return [dict(name='max-ammo-scaling-real/Emilia/'+str(t)+'s',body=dict(m.body_for(m.policy.roster_for('에밀리아'),t),burst_gauge_mode='accumulate'),contract=dict(duration=t)) for t in (3,30)]
