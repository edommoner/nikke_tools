"""Select original profiles with complete runtime recipient-order observation."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('ordered_catalogue_base',ROOT/'research/verify-original-catalogue.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_recipient_order_observation import SOURCE,prepared
STRICT_WIRE_DIMENSIONS=True;SELECTED_PREPARATION=True
MAX_SELECTED_CASES=base.MAX_SELECTED_CASES
suite=base.suite;cross=base.cross;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT
case_catalog=base.case_catalog;native_reference=base.native_reference;compare=base.compare
validate_rejection=base.validate_rejection

def prepare():raise ValueError('Select explicit original catalogue cases')
def prepare_selected(names):return prepared(base.prepare_selected(names))
