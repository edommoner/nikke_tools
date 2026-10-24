"""Coordinate pool collection and release using shared native/runtime adapters."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('accum_coordinate_quantity',ROOT/'research/verify-coordinate-quantity-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_accum_emission_cases import fixtures
from world_damage_accum_native import capture
from world_coordinate_packet_quantity_native import observe
from world_frame_native import roster_names
from portable_damage_accum_observation import compare_final
SOURCE=parent.SOURCE;INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross;compile_case=parent.compile_case;validate_rejection=parent.validate_rejection

def prepare():
    entries,_=parent.prepare()
    for case in fixtures():
        words,meta,bindings,descriptors=compile_case(case);entries.append((case['name'],words,(case,meta,bindings,descriptors)))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()

def native_reference(domain):
    case=domain[0]
    if not case['name'].startswith('coordinate-accum-emission/'):return parent.native_reference(domain)
    with capture(roster_names(case),identity_rows=True) as accumulation:result=observe(case)
    result['damage_accumulation']=accumulation
    return result

def compare(block,domain):
    if not domain[0]['name'].startswith('coordinate-accum-emission/'):return parent.compare(block,domain)
    expected=native_reference(domain);plain=dict(expected);accumulation=plain.pop('damage_accumulation')
    parent.compare_expected(block,domain,plain,verify_parent_quantity=False);compare_final(block,domain[1],accumulation)
    return expected
