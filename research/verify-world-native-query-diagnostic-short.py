"""Read-only first-query census/window for the original Lily30s input; not a battle proof."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('native_query_diagnostic_base',ROOT/'research/verify-world-state-focus-rosters-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from world_late_attack_random_native import capture_queries
from portable_query_diagnostic import decode,native_misses,compare_misses,decode_census,native_census,compare_census


def prepare():
    entries,_=base.prepare();entries=[e for e in entries if e[0]=='state-focus-real/릴리/30s']
    assert len(entries)==1
    data=array.array('I',[1]);data.extend(entries[0][1])
    if sys.byteorder!='little':data.byteswap()
    return entries,data.tobytes()


def native_reference(domain):
    case=domain[0];names=case['body']['squad']
    with capture_queries(names,with_selectors=True) as (queries,samples):native,trace=base.base.real.native_reference(case['body'])
    return dict(proof_kind='read-only numeric-query-observation',battle_certified=False,
                native_only_context=dict(battle_sha256=cross.digest(native),skill_trace_sha256=cross.digest(trace),friendly_samples=len(samples)),
                numeric_query_census=native_census(queries),numeric_query_misses=native_misses(queries,names))


def compare(block,domain):
    assert block[0]==0,'diagnostic GPU computation status'
    expected=native_reference(domain)
    from portable_specs import LIMITS as L
    if block[L['NATIVE_DIAG_BASE']]==0x4e514331:compare_census(decode_census(block),expected['numeric_query_census'])
    else:compare_misses(decode(block),expected['numeric_query_misses'])
    return expected
