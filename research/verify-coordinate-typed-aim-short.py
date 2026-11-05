"""Retain all46 and connect declared frame aims to real sampled typed weapons."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('typed_aim_weapon_parent',ROOT/'research/verify-coordinate-typed-weapon-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_typed_aim_gpu_cases import fixtures
from portable_coordinate_typed_weapon_cases import prepare as prepare_case
from portable_coordinate_typed_input import compile_coordinate_typed
from portable_coordinate_typed_specs import COORDINATE_OUTPUT_WORDS
SOURCE='gpu/world_coordinate_typed_aim_entry.slang';suite=parent.suite;cross=parent.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT

def prepare():
    rows,_=parent.prepare()
    for row in fixtures():
        c,p=prepare_case(row);c['coordinate_packet_history']='ordered-sha256-v1';c['python_observers_only']=True
        w,m,b,d=compile_coordinate_typed(p,c['typed_bindings'],probe_kind=c['typed_bindings'][0]['kind'],geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True)
        rows.append((c['name'],w,(c,m,b,d)))
    seed=rows[-len(fixtures())+3][1]
    for label,offset,value in [('flag',109968+14,2),('weapon-required',109968+13,0),('live-required',109968+11,0),('slot-overflow',108792+32,257),('slot-undeclared',108792+32,255),('disabled-typed-slot',109968+14,0)]:
        w=list(seed);w[offset]=value;rows.append(('reject/typed-aim/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    if not domain[0].get('typed_aim_policy'):return parent.native_reference(domain)
    from world_coordinate_typed_aim_native import observe
    from portable_coordinate_typed_aim_contracts import verify
    n,_=observe(domain[0]);verify(domain[0],n);return n

def compare(block,domain):
    if not domain[0].get('typed_aim_policy'):return parent.compare(block,domain)
    from world_coordinate_sampled_skill_native import creation_indices
    from portable_coordinate_typed_weapon_comparison import compare as compare_weapons
    from portable_coordinate_typed_aim_comparison import compare as compare_aims,HEAD,END
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    return compare_observed(block,domain,n,indices)

def compare_observed(block,domain,n,indices):
    from portable_coordinate_typed_weapon_comparison import compare as compare_weapons
    from portable_coordinate_typed_aim_comparison import compare as compare_aims,HEAD,END
    parent.original.compare_observed(block[:COORDINATE_OUTPUT_WORDS],domain,n,indices)
    # Existing physical consumer retains its complete unused-tail assertion.
    # The separate declared aim owner is checked in full before zero projection.
    compare_aims(block,domain,n);physical=list(block);physical[HEAD:END]=[0]*(END-HEAD)
    compare_weapons(physical,domain[0],n['coordinate_typed_weapon']);return n

def native_comparison_adapter(domain):
    if not domain[0].get('typed_aim_policy'):return parent
    from types import SimpleNamespace
    return SimpleNamespace(compare=compare,native_reference=native_reference)

def validate_rejection(block,name):
    if name.startswith('reject/typed-aim/'):assert block[0]==64,(name,block[0])
    else:parent.validate_rejection(block,name)
