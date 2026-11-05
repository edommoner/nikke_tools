"""One catalogue stimulus using the same compiler, oracle and GPU comparator."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ammo_equivalent_catalogue_base',ROOT/'research/verify-world-ammo-equivalent-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_ammo_equivalent_catalogue_cases import fixtures
suite,cross=base.suite,base.cross
native_reference,compare=base.native_reference,base.compare
def prepare():return base.prepare_cases(fixtures(),reject=False)
