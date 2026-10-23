"""Complete original Anis Star definitions, without rewriting skill metadata."""
import importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('skill_weapon_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return [dict(name='skill-weapon-real/Anis-Star/'+str(t)+'s',body=dict(m.body_for(m.policy.roster_for('아니스 : 스타'),t),burst_gauge_mode='accumulate'),contract=dict(duration=t)) for t in (3,30)]
