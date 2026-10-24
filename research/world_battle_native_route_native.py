"""Native router without all-enemies rewriting; original battle parity anchor."""
import importlib.util
from pathlib import Path
from world_battle_attack_group_native import observe as grouped

def observe(case):
    native,trace=grouped(case)
    if case['contract'].get('baseline_unchanged'):
        spec=importlib.util.spec_from_file_location('native_route_baseline',Path(__file__).with_name('verify-world-projectile-rosters.py'))
        real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)
        baseline,shots=real.native_reference(case['body'])
        native['baseline']=dict(battle=baseline,projectile_shots=shots)
    return native,trace
