"""Retain all long60 inputs and compare real mixed-owner groups independently."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_battle_attack_group_input import compile_battle
from portable_mixed_group_cases import fixtures
from portable_mixed_group_contracts import verify
from world_battle_native_route_native import observe
spec=importlib.util.spec_from_file_location('mixed_group_parent',ROOT/'research/verify-world-attack-group-long-short.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
SOURCE=parent.SOURCE;INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS
STRICT_WIRE_DIMENSIONS=True;suite=parent.suite;cross=parent.cross

def native_reference(domain):
    if not domain[0]['contract'].get('mixed_owners'):return parent.native_reference(domain)
    native,_=observe(domain[0]);verify(domain[0],native);return native
suite.inspect_native=lambda case:native_reference((case,))
def prepare():
    entries,_=parent.prepare()
    for case in fixtures():
        prepared=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
        words,metadata=compile_battle(prepared,routing=case['routing'],group_history='compact')
        entries.append((case['name'],words,(case,prepared,words,metadata)))
    words=list(entries[60][1]);words[104402]^=2
    entries.append(('reject/attack-group-mixed-owner-mask',words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def compare(block,domain):return parent.parent.shared.compare(block,domain,native=native_reference(domain))
validate_rejection=parent.validate_rejection
