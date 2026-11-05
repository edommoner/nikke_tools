"""Retain old35 and connect actual sampled original weapons to typed actors."""
import array,copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('typed_weapon_parent',ROOT/'research/verify-coordinate-typed-live-aim-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
s=importlib.util.spec_from_file_location('typed_weapon_original',ROOT/'research/verify-coordinate-original-short.py');original=importlib.util.module_from_spec(s);s.loader.exec_module(original)
from portable_coordinate_typed_weapon_cases import fixtures,prepare as prepare_case
from portable_coordinate_typed_input import compile_coordinate_typed
from portable_coordinate_typed_specs import INPUT_WORDS,OUTPUT_WORDS,COORDINATE_OUTPUT_WORDS
SOURCE='gpu/world_coordinate_typed_weapon_entry.slang';suite=parent.suite;cross=parent.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT

def prepare():
    rows,_=parent.prepare()
    for row in fixtures():
        c,p=prepare_case(row);c['coordinate_packet_history']='ordered-sha256-v1'
        w,m,b,d=compile_coordinate_typed(p,c['typed_bindings'],probe_kind=c['typed_bindings'][0]['kind'],geometry=c['typed_geometry'],coordinate_weapon_targets=True)
        rows.append((c['name'],w,(c,m,b,d)))
    seed=rows[-len(fixtures())][1]
    for label,offset,value in [('flag',13,2),('requires-live-aim',11,0),('requires-weapon-only',5120,0),('forbid-skill-route',5424,2)]:
        w=list(seed);w[109968+offset]=value;rows.append(('reject/typed-weapon/'+label,w,None))
    # Every observer in this profile consumes Python call/return only. Reuse
    # the existing attested C-event filter; no native event or case is skipped.
    for _,_,domain in rows:
        if domain is not None:domain[0]['python_observers_only']=True
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    if not domain[0].get('coordinate_weapon_targets'):return parent.native_reference(domain)
    from world_coordinate_typed_weapon_native import observe
    from portable_coordinate_typed_weapon_contracts import verify
    def owner(case):
        assert case is domain[0]
        n=original.native_reference(domain);return n,n['skill_trace']
    n,_=observe(domain[0],observer=owner);verify(domain[0],n);return n

def compare(block,domain):
    if not domain[0].get('coordinate_weapon_targets'):return parent.compare(block,domain)
    from world_coordinate_sampled_skill_native import creation_indices
    from portable_coordinate_typed_weapon_comparison import compare as typed_compare
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    original.compare_observed(block[:COORDINATE_OUTPUT_WORDS],domain,n,indices)
    typed_compare(block,domain[0],n['coordinate_typed_weapon']);return n

def native_comparison_adapter(domain):
    # Old domains delegate their actual compare call site to the retained
    # adapter. The live-parent cache must patch that owner, not this wrapper.
    if not domain[0].get('coordinate_weapon_targets'):return parent
    from types import SimpleNamespace
    return SimpleNamespace(compare=compare,native_reference=native_reference)

def validate_rejection(block,name):
    if name.startswith('reject/typed-weapon/'):assert block[0]==64,(name,block[0])
    else:parent.validate_rejection(block,name)
