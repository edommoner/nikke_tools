"""Direct late numeric reads and lazy controls through the full common runtime."""
import array,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('late_random_base',ROOT/'research/verify-world-heal-share-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_late_attack_random_cases import fixtures
from portable_late_attack_random_contracts import verify
from world_late_attack_random_native import observe
from portable_revival_specs import BASE,RNG,TRACE,TRACE_COUNT
from portable_ordered_history import friendly_records,verify_history


def prepare():
    entries=[]
    for case in fixtures():
        case['environment']['allied_seed']=case['seed']
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    from portable_specs import LIMITS as L
    meta=L['RECIPIENT_META_BASE'];seed=entries[0][1]
    for label,at,value,index in [('missing-tag',meta+5,0,0),('bad-tag',meta+5,1,0),
                                ('missing-allied-tag',meta+2,0,0),('unneeded-tag',meta+5,0x4e515231,3),
                                ('reserved',meta+6,2,0),('log-without-native-tag',meta+6,1,3),('no-combat',3,0,0),
                                ('excessive-count',L['RECIPIENT_BASE']+8+1,6,0)]:
        words=list(entries[index][1]);words[at]=value
        entries.append(('reject/native-query-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    case=domain[0];native,trace=observe(case);verify(case,native)
    samples=native.pop('late_attack_random')['samples']
    return dict(battle=native,skill_trace=trace,friendly_samples=samples)


def compare(block,domain):
    assert block[0]==0,(domain[0]['name'],'GPU status',block[0])
    expected=native_reference(domain)
    base.compare_expected(block,domain,expected)
    verify_history(block,friendly_records(expected['friendly_samples'],owner=4,selector=19))
    state=(3,tuple(block[RNG+8:RNG+632])+(block[RNG],),None)
    digest=hashlib.sha256(json.dumps(state,separators=(',',':')).encode()).hexdigest()
    assert digest==expected['friendly_samples'][-1]['after_sha256'],'complete MT state'
    return expected


def validate_rejection(block,name):
    assert name.startswith('reject/native-query-') and block[0]==64
