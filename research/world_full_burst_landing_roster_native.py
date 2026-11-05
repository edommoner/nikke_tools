"""Actual original-profile cast and landing handler observations."""
import importlib.util
from pathlib import Path
from world_full_burst_landing_native import capture

def observe(case):
    s=importlib.util.spec_from_file_location('landing_real_native',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    with capture(case['body']['squad']) as o:n,shots=m.native_reference(case['body'])
    return dict(battle=n,projectile_shots=shots,full_burst_landing=o),[]
