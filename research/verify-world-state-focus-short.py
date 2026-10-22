"""Shared cover/camera predicates and live-marker aim against full native battles."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('state_focus_base',ROOT/'research/verify-world-heal-share-short.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_state_predicate_cases import fixtures as predicates
from portable_state_predicate_contracts import verify as verify_predicates
from world_state_predicate_native import observe as observe_predicates
from portable_focus_aim_cases import fixtures as aims
from world_focus_aim_native import observe as observe_aims
from portable_focus_aim_contracts import verify as verify_aims
from portable_specs import LIMITS as L


def fixtures():return predicates()+aims()


def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    focus=next(words for name,words,_ in entries if name=='state-predicate-focus-passive-self')
    cover=entries[0][1];aim=next(words for name,words,_ in entries if name=='focus-aim-all-aim-only')
    condition=L['CONDITION_BASE']+L['CONDITION_WORDS'];definition=L['DEFINITION_BASE']+L['DEFINITION_WORDS']
    from portable_specs import FIELDS as F
    mutations=[('focus-name',focus,[(condition+1,1)]),('focus-argument',focus,[(condition+3,0x3ff00000)]),
        ('cover-name',cover,[(condition+1,1)]),('cover-nan',cover,[(condition+3,0x7ff80000)]),
        ('no-combat',focus,[(3,0)]),('bad-policy',aim,[(L['WORLD_META_BASE']+4,1)]),
        ('missing-policy',aim,[(L['WORLD_META_BASE']+4,0)]),
        ('marker-health-scaling',aim,[(L['HEALTH_DEFINITION_BASE']+L['HEALTH_DEFINITION_WORDS'],1)]),
        ('marker-interval',aim,[(definition+F['INTERVAL']+1,0x3ff00000)]),
        ('physical-interrupt',aim,[(L['WEAPON_BASE']+1,0)]),
        ('cover-passive',cover,[(L['EVENT_BASE']+L['EVENT_WORDS'],0),(L['EVENT_BASE']+L['EVENT_WORDS']+6,1)]),
        ('policy-reserved',aim,[(L['WORLD_META_BASE']+5,1)])]
    for name,seed,changes in mutations:
        words=list(seed)
        for at,value in changes:words[at]=value
        if name=='cover-passive':
            from portable_trigger_specs import pack_event_candidates
            pack_event_candidates(words,L)
        entries.append(('reject/state-focus-'+name,words,None))
    return entries,pack(entries)


def pack(entries):
    data=array.array('I',[len(entries)])
    for _,words,_ in entries:data.extend(words)
    if sys.byteorder!='little':data.byteswap()
    return data.tobytes()


def native_reference(domain):
    case=domain[0]
    if case['name'].startswith('state-predicate-'):
        native,trace=observe_predicates(case);verify_predicates(case,native);native.pop('state_predicates')
        return dict(battle=native,skill_trace=trace)
    native,trace=observe_aims(case);verify_aims(case,native);rows=native.pop('focus_aim')
    assert rows,(case['name'],'pre-weapon aim observation')
    return dict(battle=native,skill_trace=trace,focus_aim=rows)


def compare(block,domain):
    assert block[0]==0,(domain[0]['name'],'GPU status',block[0])
    expected=native_reference(domain);base.compare_expected(block,domain,expected)
    if 'focus_aim' in expected:
        from calculator.boss_pattern import AIM_ADDS
        head=L['FOCUS_STATE_BASE'];packed=block[head]|(block[head+1]<<32)
        labels={0:'',128:AIM_ADDS,**{i:b.label for i,b in enumerate(domain[2]) if i}}
        actual=[labels[(packed>>(8*i))&255] for i in range(5)];last=expected['focus_aim'][-1]
        assert actual==last['aims'],(domain[0]['name'],'frame aim snapshot',actual,last)
        assert block[head+2]==last['camera'] and bool(block[head+3])==last['full_burst']
        assert block[head+6]==0x46414331 and block[head+7]==0
    return expected


def validate_rejection(block,name):
    assert name.startswith("reject/state-focus-") and block[0]==64
