"""Reuse the shared owner executor and complete physical/aim comparisons."""
import array
import importlib.util
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('original_projectile_owner_base',ROOT/'research/verify-coordinate-typed-owner-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_original_projectile_weapon_cases import fixtures,prepare as prepare_case
from portable_coordinate_typed_input import compile_coordinate_typed
SOURCE=base.SOURCE;suite=base.suite;cross=base.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT

def prepare():
    rows=[]
    for case in fixtures():
        c,p=prepare_case(case)
        w,m,b,d=compile_coordinate_typed(p,c['typed_bindings'],probe_kind=2,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True)
        rows.append((c['name'],w,(c,m,b,d)))
    for label,offset,value in [('owner-marker',12,0),('actor-policy',15,1),('owner-generation',2328+7,2),('axis-invalid',5168,99),('unused-axis',5168+255,2)]:
        w=list(rows[0][1]);w[109968+offset]=value;rows.append(('reject/original-projectile-weapons/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    from world_coordinate_typed_owner_native import observe
    from portable_original_projectile_weapon_contracts import verify
    n,_=observe(domain[0]);return verify(domain[0],n)

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    return base.parent.parent.compare_observed(block,domain,n,indices)

def validate_rejection(block,name):
    assert name.startswith('reject/original-projectile-weapons/')
    assert block[0]==64,(name,block[0])
