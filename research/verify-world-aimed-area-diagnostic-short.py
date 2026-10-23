"""All area battles and complete direct private receipts, including scatter36."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('aimed_area_diag_base',ROOT/'research/verify-world-aimed-area-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross,prepare,native_reference=base.suite,base.cross,base.prepare,base.native_reference
validate_rejection=base.validate_rejection
from portable_interrupt_aim_trace import gpu_records
from world_frame_native import roster_names


def compare(block,domain):
    expected=native_reference(domain);base.compare_expected(block,domain,expected)
    actual=gpu_records(block,roster_names(domain[0]));labels={b.identity:b.label for b in domain[2] if int(b.kind)==6}
    for row in actual:row['label']=labels[row['target']['identity']]
    assert actual==expected['interrupt_landings'],(domain[0]['name'],'all direct area receipts',actual,expected['interrupt_landings'])
    return expected
