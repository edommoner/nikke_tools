"""Actual complete-profile native battle and query-free healing observations."""
import importlib.util
from pathlib import Path
import engine_worker
from world_heal_charge_native import capture

def bare(case):
    s=importlib.util.spec_from_file_location('healing_real_native',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    n,shots=m.native_reference(case['body']);return dict(battle=n,projectile_shots=shots),[]
def observe(case):
    with capture(case['body']['squad'],record_final=True,tag_effects=True) as o:n,t=bare(case)
    n['healing_charge']=o;return n,t
