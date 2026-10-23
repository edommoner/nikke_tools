"""Concurrent caches and battle consumers, with complete ordered friendly history."""
import array,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('mixed_base',ROOT/'research/verify-world-heal-share-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_mixed_query_cases import fixtures
from portable_mixed_query_contracts import verify
from world_mixed_query_native import observe
from portable_ordered_history import friendly_records,verify_history
from portable_revival_specs import RNG
from portable_specs import LIMITS as L


def prepare():
    entries=[]
    for case in fixtures():
        case['environment']['allied_seed']=case['seed']
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native)
    samples=native.pop('mixed_query')['samples'];focus=native.pop('focus_aim')
    events=native.pop('heal_share_events')
    return dict(battle=native,skill_trace=trace,friendly_samples=samples,focus_aim=focus,heal_share_events=events)


def compare_expected(block,domain,expected):
    base.compare_expected(block,domain,expected)
    verify_history(block,friendly_records(expected['friendly_samples']))
    state=(3,tuple(block[RNG+8:RNG+632])+(block[RNG],),None)
    digest=hashlib.sha256(json.dumps(state,separators=(',',':')).encode()).hexdigest()
    assert digest==expected['friendly_samples'][-1]['after_sha256'],'complete MT state'
    from calculator.boss_pattern import AIM_ADDS
    head=L['FOCUS_STATE_BASE'];packed=block[head]|block[head+1]<<32
    labels={0:'',128:AIM_ADDS,**{i:b.label for i,b in enumerate(domain[2]) if i}}
    actual=[labels[(packed>>(8*i))&255] for i in range(5)];last=expected['focus_aim'][-1]
    assert actual==last['aims'],(domain[0]['name'],'final focus snapshot',actual,last)
    assert block[head+2]==last['camera'] and bool(block[head+3])==last['full_burst']
    assert block[head+6]==0x46414331 and block[head+7]==0
    return expected


def compare(block,domain):return compare_expected(block,domain,native_reference(domain))


def validate_rejection(block,name):raise AssertionError('No rejection inputs in mixed-query suite')
