"""Additional ammo-instant stimuli, reusing the shared adapter and comparator."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mode_capacity_instant_base',ROOT/'research/verify-world-mode-capacity-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross,native_reference,compare=base.suite,base.cross,base.native_reference,base.compare

def prepare():return base.prepare_cases([c for c in base.all_fixtures() if c['name'].startswith('mode-capacity-instant-')],raw_rejections=False)
