"""The complete106 logical-owner battle suite with resource-backed arc storage."""
import importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('resident_arc_parent',ROOT/'research/verify-coordinate-typed-owner-hp-death-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_resident_arc_specs import SOURCE,INPUT_WORDS,OUTPUT_WORDS,PREFIX_WORDS,check_layout
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)
cross=parent.cross;STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT

def prepare():
    check_layout(ROOT)
    return parent.prepare()
def native_reference(domain):return parent.native_reference(domain)
def logical(block):
    assert len(block)==OUTPUT_WORDS,'Complete resident arc wire required'
    assert not any(block[PREFIX_WORDS:]),'Resident arc scratch leaked'
    return block[:PREFIX_WORDS]
def compare(block,domain):
    adapter=parent.native_comparison_adapter(domain)
    return adapter.compare(logical(block),domain)
def native_comparison_adapter(domain):return SimpleNamespace(compare=compare,native_reference=native_reference)
def validate_rejection(block,name):parent.validate_rejection(logical(block),name)
