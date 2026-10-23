"""All authored aimed area packets and final native pool/accounting quantities."""
import array,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('aimed_area_base',ROOT/'research/verify-world-heal-share-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_aimed_area_cases import fixtures
from portable_aimed_area_contracts import verify
from world_aimed_area_native import observe
from portable_specs import LIMITS as L


def prepare():
    rows=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case);rows.append((case['name'],words,(case,metadata,bindings)))
    packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()


def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native)
    rows=native.pop('interrupt_landings');focus=native.pop('focus_aim');packets=native.pop('physical_packet_sets');account=native.pop('parts_skill_accounting')
    native.pop('parts_skill_events')
    return dict(battle=native,skill_trace=trace,interrupt_landings=rows,focus_aim=focus,physical_packet_sets=packets,interrupt_accounting=account)


def compare_expected(block,domain,expected):
    base.compare_expected(block,domain,expected)
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    extra=[]
    for slot,b in enumerate(domain[2]):
        generation=block[L['WORLD_ACTOR_POOL_STATE_BASE']+slot*16]
        if int(b.kind)!=6 or generation==0:continue
        at=L['COUNTER_LANDING_EXTRA_BASE']+slot*4
        extra.append(dict(identity=b.identity,generation=generation,extra_hits=block[at],extra_dealt=number(at+2)))
    actual=dict(interrupt_damage=[number(785424+i*2) for i in range(5)],extra=extra)
    assert actual==expected['interrupt_accounting'],(domain[0]['name'],'complete direct+extra interruption accounting',actual,expected['interrupt_accounting'])
    from calculator.boss_pattern import AIM_ADDS
    head=L['FOCUS_STATE_BASE'];packed=block[head]|block[head+1]<<32;labels={0:'',128:AIM_ADDS,**{i:b.label for i,b in enumerate(domain[2]) if i}}
    last=expected['focus_aim'][-1]
    assert [labels[(packed>>(8*i))&255] for i in range(5)]==last['aims'],'final focus snapshot'
    assert block[head+2]==last['camera'] and bool(block[head+3])==last['full_burst'] and block[head+6]==0x46414331 and block[head+7]==0
    return expected


def compare(block,domain):return compare_expected(block,domain,native_reference(domain))


def validate_rejection(block,name):raise AssertionError('No raw rejections in aimed area suite')
