"""Complete original Modernia profile, with natural accuracy-gated activations."""
import importlib.util
from pathlib import Path


def fixtures():
    spec=importlib.util.spec_from_file_location('accuracy_roster_factory',Path(__file__).resolve().parent/'verify-world-projectile-rosters.py');real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
    rows=[]
    for duration,checks,shots in ((3,0,112),(30,8,2343)):
        body=dict(real.body_for(real.policy.roster_for('모더니아'),duration),burst_gauge_mode='accumulate')
        rows.append(dict(name='accuracy-predicate-real-'+str(duration)+'s',character='모더니아',effect_name='대도약 2',body=body,contract=dict(checks=checks,queries=checks,activations=checks,values=([14.]*5+[5.44]*3 if checks else []),shots=shots)))
    return rows
