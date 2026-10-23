"""Full Red Hood profile, ordinary automatic accumulated-gauge battles."""
from pathlib import Path
import importlib.util


def fixtures():
    s=importlib.util.spec_from_file_location('squad_stage_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));real=importlib.util.module_from_spec(s);s.loader.exec_module(real)
    rows=[dict(name='squad-stage-real/레드 후드/'+str(duration)+'s',character='레드 후드',favorite_stage=0,duration=duration,body=dict(real.body_for(real.policy.roster_for('레드 후드'),duration),burst_gauge_mode='accumulate')) for duration in (3,30)]
    import copy
    for original in list(rows):
        case=copy.deepcopy(original);case['name']+='/explicit-A';case['burst_stages']={'레드 후드':'A'};rows.append(case)
    for original in list(rows[:2]):
        case=copy.deepcopy(original);case['name']+='/live-A';case['live_overrides']=[dict(owner='레드 후드',stage='A',duration=-1)];rows.append(case)
    case=copy.deepcopy(rows[0]);case['name']+='/expired-A';case['live_overrides']=[dict(owner='레드 후드',stage='A',duration=1)];rows.append(case)
    return rows
