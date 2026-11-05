"""Retain99 and verify generation-bound fields across real ADD graph lifetimes."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('add_lifetime_parent',ROOT/'research/verify-coordinate-typed-logical-owner-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_typed_owner_add_lifetime_cases import fixtures,prepare as prepare_case
from portable_coordinate_typed_input import compile_coordinate_typed
SOURCE=parent.SOURCE;suite=parent.suite;cross=parent.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT

# The existing sampled battle/field comparator, without new exclusions.
compare_observed=parent.parent.parent.parent.parent.compare_observed

def prepare():
    rows,_=parent.prepare()
    for row in fixtures():
        c,p=prepare_case(row);c['coordinate_packet_history']='ordered-sha256-v1';c['python_observers_only']=True
        w,m,b,d=compile_coordinate_typed(p,c['typed_bindings'],probe_kind=c['owner_add_lifetime']['kind'],geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True,coordinate_logical_owners=True)
        rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    if not domain[0].get('owner_add_lifetime'):return parent.native_reference(domain)
    from world_coordinate_typed_owner_add_lifetime_native import observe
    from portable_coordinate_typed_owner_add_lifetime_contracts import verify
    n,_=observe(domain[0]);verify(domain[0],n);return n

def compare(block,domain):
    if not domain[0].get('owner_add_lifetime'):return parent.compare(block,domain)
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    return compare_observed(block,domain,n,indices)

def native_comparison_adapter(domain):
    if not domain[0].get('owner_add_lifetime'):return parent
    return SimpleNamespace(compare=compare,native_reference=native_reference)

def validate_rejection(block,name):parent.validate_rejection(block,name)
