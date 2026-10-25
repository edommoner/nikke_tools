"""Same full original comparator, with source-row identities for equal labels."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('periodic_original_parent',ROOT/'research/verify-coordinate-original-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_original_periodic_cases import fixtures
from portable_coordinate_original_cases import prepare_case
suite=parent.suite;cross=parent.cross;SOURCE=parent.SOURCE;INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
native_reference=parent.native_reference;compile_coordinate_battle=parent.compile_coordinate_battle
def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def compare(block,domain):
    # Keep the existing comparator's live-parent cache call site intact.
    n=parent.compare(block,domain)
    if domain[0]['duration']==30:
        assert n['skill_trace'],'Original long periodic case must actually land damage'
        assert any(domain[0]['effects'][r['row']].get('tick_interval') for r in n['skill_trace']),'Original periodic source must actually fire'
    return n
def native_comparison_adapter(domain):return parent
def validate_rejection(block,name):raise AssertionError('No original periodic definition may be discarded')
