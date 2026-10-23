"""Real native battle, physical shots and existing selection returns."""
import importlib.util
from pathlib import Path
from world_leftmost_native import capture

def observe(case):
    s=importlib.util.spec_from_file_location('leftmost_real_oracle',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    with capture(case['body']['squad']) as selections:n,shots=m.native_reference(case['body'])
    return dict(battle=n,projectile_shots=shots,leftmost_selections=selections),[]
