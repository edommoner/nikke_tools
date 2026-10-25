"""Focused mode/control cases against the existing shared battle executor."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('mode_actions_parent',ROOT/'research/verify-coordinate-burst-control-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_mode_actions_cases import fixtures
SOURCE='gpu/world_coordinate_mode_actions_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross;native_reference=parent.native_reference
compare=parent.compare;validate_rejection=parent.validate_rejection
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
native_comparison_adapter=parent.native_comparison_adapter

def compile_case(case):
    from world_coordinate_mode_actions_contracts import validate
    validate(case);return parent.compile_case(case)

def prepare():
    rows,_=parent.prepare()
    for c in fixtures():
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
