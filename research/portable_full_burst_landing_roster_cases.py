"""Original Elegg Boom and Shock definitions without temporal rewriting."""
import importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('landing_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return [dict(name='full-burst-landing-real/Elegg-Boom-Shock/'+str(t)+'s',body=dict(m.body_for(m.policy.roster_for('일레그 : 붐 앤 쇼크'),t),burst_gauge_mode='accumulate'),contract=dict(duration=t)) for t in (3,30)]
