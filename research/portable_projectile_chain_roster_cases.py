"""All original Rapi: Red Hood definitions at3/30s, no effect rewrites."""
import importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('projectile_chain_original_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return [dict(name='projectile-chain-real/Rapi-red-hood/'+str(t)+'s',body=dict(m.body_for(m.policy.roster_for('라피 : 레드 후드'),t),burst_gauge_mode='accumulate'),contract=dict(duration=t,profile='라피 : 레드 후드')) for t in (3,30)]
