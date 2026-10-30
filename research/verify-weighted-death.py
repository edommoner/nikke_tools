"""The same full arena and weighted banks, with original death witnesses."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('weighted_death_parent',ROOT/'research/verify-weighted-battle.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_weighted_death_cases import fixtures
SOURCE=base.SOURCE;suite=base.suite;cross=base.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT
native_reference=base.native_reference;compare=base.compare;validate_rejection=base.validate_rejection
def prepare():return base.prepare_cases(fixtures(),condition_negatives=False)
