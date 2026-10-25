"""Focused automatic-reload contract on the existing shared GPU executor."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('auto_reload_parent',ROOT/'research/verify-coordinate-mode-actions-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_auto_reload_cases import fixtures
from portable_specs import LIMITS as L
SOURCE='gpu/world_coordinate_auto_reload_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True;suite=parent.suite;cross=parent.cross
compile_case=parent.compile_case;native_reference=parent.native_reference;validate_rejection=parent.validate_rejection
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT;native_comparison_adapter=parent.native_comparison_adapter

def prepare():
    rows,_=parent.prepare()
    for c in fixtures():
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def compare(block,domain):
    n=parent.compare(block,domain)
    if domain[0].get('observe_auto_reload'):
        for who,row in enumerate(n['manual_actions']['characters']):
            assert block[L['WEAPON_STATE_BASE']+who*L['WEAPON_STATE_WORDS']+13]==int(row['pending_auto_reload']),'Actual final automatic-reload latch'
    return n
