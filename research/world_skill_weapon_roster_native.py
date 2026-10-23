"""Full-profile canonical result and actual periodic-skill calculator calls."""
import importlib.util
from pathlib import Path
from world_skill_weapon_native import capture

def observe(case):
    s=importlib.util.spec_from_file_location('skill_weapon_real_oracle',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    with capture(case['body']['squad']) as calls:n,shots=m.native_reference(case['body'])
    return dict(battle=n,projectile_shots=shots,skill_weapon_calls=calls),[]
