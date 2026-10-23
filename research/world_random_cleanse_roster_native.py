"""Original native roster battle with transparent cleanse observation."""
import importlib.util
from pathlib import Path
from world_random_cleanse_native import capture

def observe(case):
    s=importlib.util.spec_from_file_location('random_cleanse_real_native',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    with capture(case['body']['squad']) as recorded:n,shots=m.native_reference(case['body'])
    return dict(battle=n,projectile_shots=shots,random_cleanse=recorded),[]
