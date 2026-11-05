"""Private physical interrupt native contracts through the common battle runtime."""
import array,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('interrupt_aim_base',ROOT/'research/verify-world-heal-share-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_interrupt_aim_cases import fixtures
from portable_interrupt_aim_contracts import verify
from world_interrupt_aim_native import observe
from world_frame_native import roster_names
from portable_specs import LIMITS as L


def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native)
    rows=native.pop('interrupt_landings');focus=native.pop('focus_aim')
    return dict(battle=native,skill_trace=trace,interrupt_landings=rows,focus_aim=focus)


def compare_expected(block,domain,expected):
    base.compare_expected(block,domain,expected)
    names=roster_names(domain[0]);rows=expected['interrupt_landings']
    expected_totals=[sum(r['damage'] for r in rows if r['attacker']==name) for name in names]
    actual=[struct.unpack('<d',struct.pack('<II',*block[785424+i*2:785426+i*2]))[0] for i in range(5)]
    assert actual==expected_totals,(domain[0]['name'],'private interrupt accounting',actual,expected_totals)
    from calculator.boss_pattern import AIM_ADDS
    head=L['FOCUS_STATE_BASE'];packed=block[head]|block[head+1]<<32
    labels={0:'',128:AIM_ADDS,**{i:b.label for i,b in enumerate(domain[2]) if i}}
    assert [labels[(packed>>(8*i))&255] for i in range(5)]==expected['focus_aim'][-1]['aims'],'final focus snapshot'
    assert block[head+2]==expected['focus_aim'][-1]['camera'] and bool(block[head+3])==expected['focus_aim'][-1]['full_burst']
    assert block[head+6]==0x46414331 and block[head+7]==0
    return expected


def compare(block,domain):return compare_expected(block,domain,native_reference(domain))


def validate_rejection(block,name):raise AssertionError('No raw rejections in private interrupt suite')
