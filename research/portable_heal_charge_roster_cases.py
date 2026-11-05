"""Complete original Delta ninja-thief definitions, without timing/effect rewrites."""
import importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('healing_delta_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    rows=[]
    for defender in (False,True):
        squad=m.policy.roster_for('델타 : 닌자 시프')
        if defender:squad[3]='노아'
        for duration in (3,30):
            rows.append(dict(name='heal-charge-real/Delta-ninja-thief/'+('defender' if defender else 'control')+'/'+str(duration)+'s',body=dict(m.body_for(squad,duration),burst_gauge_mode='accumulate'),contract=dict(duration=duration,defender=defender,definitions=81 if defender else 79)))
    return rows
