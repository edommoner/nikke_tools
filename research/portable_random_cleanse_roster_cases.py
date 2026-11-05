"""Original Cocoa full definitions at short and sustained battle durations."""
import importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('random_cleanse_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return [dict(name='random-cleanse-real/Cocoa/'+str(t)+'s',body=dict(m.body_for(m.policy.roster_for('코코아'),t),burst_gauge_mode='accumulate'),contract=dict(duration=t,owner=0)) for t in (3,30)]
