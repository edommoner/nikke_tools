"""Eight native direct target-factor contracts on the common battle decoder."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('aimed_factor_base',ROOT/'research/verify-world-interrupt-aim-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_aimed_packet_cases import direct_fixtures
from portable_aimed_packet_contracts import verify
from world_aimed_packet_native import observe


def prepare():
    rows=[]
    for case in direct_fixtures():
        words,metadata,bindings=suite.compile_case(case)
        rows.append((case['name'],words,(case,metadata,bindings)))
    packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()


def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native)
    rows=native.pop('interrupt_landings');focus=native.pop('focus_aim');packets=native.pop('physical_packet_sets')
    return dict(battle=native,skill_trace=trace,interrupt_landings=rows,focus_aim=focus,physical_packet_sets=packets)


def compare(block,domain):return base.compare_expected(block,domain,native_reference(domain))


def validate_rejection(block,name):raise AssertionError('No raw rejection inputs in aimed factor suite')
