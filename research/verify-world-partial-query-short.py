"""Shared battle/trace, complete RNG order and final MT for tap query consumers."""
import array,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('partial_query_base',ROOT/'research/verify-world-partial-charge-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_partial_query_cases import fixtures
from portable_partial_query_contracts import verify
from world_partial_query_native import observe
from portable_partial_charge_state import validate_state
from portable_ordered_history import friendly_records,verify_history
from portable_revival_specs import RNG


def prepare():
    rows=[]
    for c in fixtures():
        words,metadata,bindings=suite.compile_case(c);rows.append((c['name'],words,(c,metadata,bindings)))
    packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()


def native_reference(domain):
    c=domain[0];native,trace=observe(c);verify(c,native,trace)
    queries=native.pop('partial_query');notices=native.pop('nonfull_charge')
    return dict(battle=native,skill_trace=trace,partial_query=queries,notices=notices)


def compare(block,domain):
    c,metadata,bindings=domain;expected=native_reference(domain)
    validate_state(block,metadata['_control_policy']);actual=suite.decoded(block,metadata,c,bindings)
    changed=[k for k in expected['battle'] if k!='scope' and actual[k]!=expected['battle'][k]]
    assert block[0]==0 and not changed,(c['name'],block[0],changed)
    assert suite.reload.charge.team.skill_trace(block,metadata)==expected['skill_trace'],(c['name'],'full skill trace')
    samples=expected['partial_query']['samples'];verify_history(block,friendly_records(samples))
    assert samples,'Each contract must exercise real random sampling'
    state=(3,tuple(block[RNG+8:RNG+632])+(block[RNG],),None)
    digest=hashlib.sha256(json.dumps(state,separators=(',',':')).encode()).hexdigest()
    assert digest==samples[-1]['after_sha256'],(c['name'],'complete MT state')
    return expected


def validate_rejection(block,name):raise AssertionError('No raw rejections in partial-query suite')
