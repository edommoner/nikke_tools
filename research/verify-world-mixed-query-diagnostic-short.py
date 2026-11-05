"""Same mixed battles with exact native shared-healing call order."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mixed_diagnostic_base',ROOT/'research/verify-world-mixed-query-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross,prepare,native_reference=base.suite,base.cross,base.prepare,base.native_reference
validate_rejection=base.validate_rejection
from portable_heal_share_trace import native_records,gpu_records


def compare(block,domain):
    expected=native_reference(domain);base.compare_expected(block,domain,expected)
    assert gpu_records(block,observe_heal_sources=True)==native_records(expected['heal_share_events']),(domain[0]['name'],'shared healing call order')
    return expected
