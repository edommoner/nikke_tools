"""Original complete Asuka WILLE profile at short and active-removal durations."""
import importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('named_removal_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return [dict(name='named-enemy-removal-real/Asuka-WILLE/'+str(t)+'s',body=dict(m.body_for(m.policy.roster_for('아스카 : WILLE'),t),burst_gauge_mode='accumulate'),contract=dict(duration=t,dispatches=0 if t==3 else 1,ended=0 if t==3 else 1)) for t in (3,30)]
