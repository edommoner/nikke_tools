"""Real original-profile battle and actual live-capacity provider observations."""
import importlib.util
from pathlib import Path
import engine_worker
from world_max_ammo_scaling_native import capture
def bare(case):
    s=importlib.util.spec_from_file_location('max_ammo_real_native',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    n,shots=m.native_reference(case['body']);return dict(battle=n,projectile_shots=shots),[]
def observe(case):
    with capture(case['body']['squad']) as o:n,t=bare(case)
    n['max_ammo_scaling']=o;return n,t
