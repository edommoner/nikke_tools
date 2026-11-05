"""Same43 programs and battle comparator, plus observed heal call order."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('heal_diag_base',ROOT/'research/verify-world-heal-share-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross,prepare=base.suite,base.cross,base.prepare
validate_rejection=base.validate_rejection
from portable_heal_share_trace import native_records,gpu_records
def native_reference(domain):
    case,_,_=domain;native,trace=base.observe(case);base.verify(case,native)
    events=native.pop('heal_share_events')
    return dict(battle=native,skill_trace=trace,heal_share_calls=native_records(events))
def compare(block,domain):
    expected=native_reference(domain);base.compare_expected(block,domain,expected)
    actual=gpu_records(block,observe_heal_sources=domain[0].get('observe_heal_sources',False))
    assert actual==expected['heal_share_calls'],(domain[0]['name'],'heal share call order',actual,expected['heal_share_calls'])
    return expected
