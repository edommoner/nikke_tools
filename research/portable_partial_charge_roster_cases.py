"""Complete Crust profiles with and without literal tap controls."""
from pathlib import Path
import importlib.util


def fixtures():
    s=importlib.util.spec_from_file_location('partial_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));real=importlib.util.module_from_spec(s);s.loader.exec_module(real)
    rows=[]
    for duration in (3,30):
        for tap in (False,True):
            body=dict(real.body_for(real.policy.roster_for('크러스트'),duration),burst_gauge_mode='accumulate')
            controls={'크러스트':dict(click=[dict(window='always',mode='tap',rate=4,release=.03)])} if tap else {}
            rows.append(dict(name='partial-real/크러스트/'+str(duration)+'s/'+('tap' if tap else 'automatic'),character='크러스트',duration=duration,body=body,shooting_controls=controls))
    return rows
