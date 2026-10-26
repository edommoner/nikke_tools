"""Retain59 and execute the original current-enemy skill with typed frame aim."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('typed_actor_parent',ROOT/'research/verify-coordinate-typed-aim-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_typed_actor_cases import fixtures
from portable_coordinate_typed_weapon_cases import prepare as prepare_case
from portable_coordinate_typed_input import compile_coordinate_typed
SOURCE='gpu/world_coordinate_typed_actor_entry.slang';suite=parent.suite;cross=parent.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT

def prepare():
    rows,_=parent.prepare()
    for row in fixtures():
        c,p=prepare_case(row);c['coordinate_packet_history']='ordered-sha256-v1';c['python_observers_only']=True
        w,m,b,d=compile_coordinate_typed(p,c['typed_bindings'],probe_kind=3,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True)
        rows.append((c['name'],w,(c,m,b,d)))
    seed=rows[-len(fixtures())][1]
    for label,offset,value in [('flag',15,2),('requires-aim',14,0),('requires-weapons',13,0),('requires-live',11,0)]:
        w=list(seed);w[109968+offset]=value;rows.append(('reject/typed-actor/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    if not domain[0].get('typed_actor_policy'):return parent.native_reference(domain)
    from world_coordinate_typed_actor_native import observe
    from portable_coordinate_typed_actor_contracts import verify
    n,_=observe(domain[0]);verify(domain[0],n);return n

def compare(block,domain):
    if not domain[0].get('typed_actor_policy'):return parent.compare(block,domain)
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    return parent.compare_observed(block,domain,n,indices)

def native_comparison_adapter(domain):
    if not domain[0].get('typed_actor_policy'):return parent
    from types import SimpleNamespace
    return SimpleNamespace(compare=compare,native_reference=native_reference)

def validate_rejection(block,name):
    if name.startswith('reject/typed-actor/'):assert block[0]==64,(name,block[0])
    else:parent.validate_rejection(block,name)
