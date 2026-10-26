"""Unchanged landing contract with resource-backed full-capacity interval views."""
import importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_coordinate_arc_arena as arena
s=importlib.util.spec_from_file_location('arena_landing_parent',ROOT/'research/verify-coordinate-landing-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
cross=parent.cross
SOURCE='gpu/coordinate_landing_arena_probe.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=arena.LANDING_OUTPUT;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)
def prepare():
    arena.check(ROOT)
    return parent.prepare()
def native_reference(domain):return parent.native_reference(domain)
def expected(domain):
    words,reference=parent.expected(domain)
    return words+[0]*arena.WORDS,reference
def compare(block,domain):
    assert len(block)==OUTPUT_WORDS
    reference=parent.compare(block[:parent.OUTPUT_WORDS],domain)
    assert not any(block[parent.OUTPUT_WORDS:]),'Landing arc arena scratch not scrubbed'
    return reference
def validate_rejection(block,name):
    assert name.startswith('reject/coordinate-landing/') and list(block)==[64]+[0]*(OUTPUT_WORDS-1)
