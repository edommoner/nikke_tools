"""Complete original roster battle with transparent native removal observation."""
import importlib.util
from pathlib import Path
from world_named_enemy_removal_native import capture
from world_named_enemy_native import capture as capture_selection

def observe(case):
    s=importlib.util.spec_from_file_location('named_removal_real_native',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    with capture(case['body']['squad']) as calls,capture_selection(case['body']['squad']) as selection:n,shots=m.native_reference(case['body'])
    return dict(battle=n,projectile_shots=shots,named_enemy_removal=dict(removals=calls,selection=selection)),[]
