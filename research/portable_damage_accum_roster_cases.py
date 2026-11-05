"""Original Dorothy/Trony profiles, all definitions and authored timing intact."""
import importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('damage_accum_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return [dict(name='damage-accum-real/'+label+'/'+str(t)+'s',body=dict(m.body_for(m.policy.roster_for(name),t),burst_gauge_mode='accumulate'),contract=dict(duration=t,profile=name)) for name,label in (('도로시','Dorothy'),('트로니','Trony')) for t in (3,30)]
