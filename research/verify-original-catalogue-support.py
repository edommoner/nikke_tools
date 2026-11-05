"""Original support profiles use the same catalogue, executor and full comparator."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('catalogue_support_base',ROOT/'research/verify-original-catalogue.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_recipient_order_observation import SOURCE,prepared as observed_prepared
STRICT_WIRE_DIMENSIONS=True;SELECTED_PREPARATION=True
MAX_SELECTED_CASES=2
suite=base.suite;cross=base.cross;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT
case_catalog=base.case_catalog
COHORT={
    'original-catalogue/hp-shield/나가/favorite-0/30s':dict(stage=2,casts=[(1,1),(2,0),(3,2)]),
    'original-catalogue/hp-shield/티아/favorite-0/30s':dict(stage=1,casts=[(1,0),(7,3),(2,1),(3,2)]),
}

def prepare():raise ValueError('Use the registered frozen support cohort')

def prepare_selected(names):
    if set(names)!=set(COHORT) or len(names)!=2:raise ValueError('Complete frozen support cohort required')
    return observed_prepared(base.prepare_selected(names))

def verify_native(case,native):
    expected=COHORT[case['name']]
    ticks=native['burst_controls']['ticks']
    assert ticks and all(t['stages'][0]==expected['stage'] for t in ticks),'Original support stage changed'
    assert ticks[-1]['cycles']>=1,'Original party must enter full burst'
    assert any(a['owner']==0 for a in native['coordinate_typed_weapon']['attacks']),'Original support must actually fire'
    return native

def verify_casts(name,trace):
    # The shared combat runtime encodes a reentered stage as stage + 6.
    casts=[(row['event'],row['owner']) for row in trace if row['event'] in (1,2,3,7,8,9)]
    expected=COHORT[name]['casts']
    assert casts[:len(expected)]==expected,'Original support must execute its real burst/reentry sequence'

def native_reference(domain):return verify_native(domain[0],base.native_reference(domain))

def compare(block,domain):
    native=verify_native(domain[0],base.compare(block,domain))
    from portable_runtime import decode
    verify_casts(domain[0]['name'],decode(block[:159744],domain[1])['burst_trace'])
    return native

validate_rejection=base.validate_rejection
