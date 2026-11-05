"""Connect original shield carriers through the same owner/physical comparator."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('original_shield_owner_base',ROOT/'research/verify-original-projectile-weapons.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_original_shield_weapon_cases import fixtures,prepare as prepare_case
compile_coordinate_typed=base.compile_coordinate_typed
SOURCE=base.SOURCE;suite=base.suite;cross=base.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT

def prepare():
    rows=[]
    for case in fixtures():
        c,p=prepare_case(case)
        w,m,b,d=compile_coordinate_typed(p,c['typed_bindings'],probe_kind=3,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True)
        if c.get('declared_manual_sequences'):m['coordinate_original_input'].update(original_controls_preserved=False,declared_manual_sequences_applied_after_identity_check=True)
        rows.append((c['name'],w,(c,m,b,d)))
    for label,offset,value in [('owner-marker',12,0),('actor-policy',15,1),('owner-generation',2328+7,2),('axis-invalid',5168,99),('unused-axis',5168+255,3)]:
        w=list(rows[0][1]);w[109968+offset]=value;rows.append(('reject/original-shield-weapons/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    from world_coordinate_typed_owner_native import observe
    from portable_original_shield_weapon_contracts import verify
    n,_=observe(domain[0]);return verify(domain[0],n)

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    return base.base.parent.parent.compare_observed(block,domain,n,indices)

def validate_rejection(block,name):
    assert name.startswith('reject/original-shield-weapons/')
    assert block[0]==64,(name,block[0])
