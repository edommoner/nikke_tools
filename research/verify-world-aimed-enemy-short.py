"""Shared full-battle and private-receipt comparator for aimed counter children."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('aimed_enemy_area',ROOT/'research/verify-world-aimed-area-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_aimed_enemy_cases import fixtures
from portable_aimed_enemy_contracts import verify
from world_aimed_area_native import observe
from portable_interrupt_aim_trace import gpu_records
from world_frame_native import roster_names


def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,metadata,bindings)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native)
    receipts=native.pop('interrupt_landings');focus=native.pop('focus_aim');packets=native.pop('physical_packet_sets');account=native.pop('parts_skill_accounting');native.pop('parts_skill_events')
    return dict(battle=native,skill_trace=trace,interrupt_landings=receipts,focus_aim=focus,physical_packet_sets=packets,interrupt_accounting=account)


def compare(block,domain):
    expected=native_reference(domain);base.compare_expected(block,domain,expected)
    actual=gpu_records(block,roster_names(domain[0]));labels={b.identity:b.label for b in domain[2] if int(b.kind)==6}
    for row in actual:row['label']=labels[row['target']['identity']]
    assert actual==expected['interrupt_landings'],(domain[0]['name'],'private receipts after callback',actual,expected['interrupt_landings'])
    return expected


def validate_rejection(block,name):raise AssertionError('No raw rejections in aimed callback suite')
