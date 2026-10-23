"""Observe actual original-profile pool operations without adding queries."""
import importlib.util
from pathlib import Path
import engine_worker
from world_damage_accum_native import capture
def bare(case):
    s=importlib.util.spec_from_file_location('damage_accum_real_native',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    n,shots=m.native_reference(case['body']);return dict(battle=n,projectile_shots=shots),[]
def observe(case):
    with capture(case['body']['squad'],tag_effects=True) as data:n,t=bare(case)
    n['damage_accumulation']=data;return n,t
