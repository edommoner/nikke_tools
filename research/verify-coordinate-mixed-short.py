"""Shared group runtime with scoped real overlay/attack/split scene inputs."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('mixed_parent',ROOT/'research/verify-coordinate-group-short.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
from portable_coordinate_mixed_cases import fixtures
from portable_coordinate_mixed_contracts import verify
from world_coordinate_mixed_native import observe
from world_coordinate_aim_native import capture
SOURCE='gpu/world_coordinate_mixed_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross;validate_rejection=parent.validate_rejection

def compile_case(case):return parent.compile_case(case,allow_world_nodes=True)
def prepare():
    entries,_=parent.prepare()
    for case in fixtures():
        w,m,b,d=compile_case(case);entries.append((case['name'],w,(case,m,b,d)))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()
def native_reference(domain):
    if '/mixed-' not in domain[0]['name']:return parent.native_reference(domain)
    with capture(domain[0]) as aim:native,trace=observe(domain[0])
    verify(domain[0],native);native['skill_trace']=trace;native['coordinate_aim']=aim
    return native
def compare(block,domain):
    if '/mixed-' not in domain[0]['name']:return parent.compare(block,domain)
    return parent.compare(block,domain,expected=native_reference(domain))
