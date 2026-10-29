"""Selected catalogue and frozen cohorts share the existing owner executor."""
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('catalogue_original_owner_base',ROOT/'research/verify-original-projectile-weapons.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_original_catalogue_cases import catalog,selected_rows,prepare as prepare_case,verify,MAX_SELECTED_CASES
from portable_skill_history import SOURCE,CAPACITY,compare_and_project
suite=base.suite;cross=base.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT
SELECTED_PREPARATION=True

def case_catalog():return list(catalog(include_roles=True))
def prepare():raise ValueError('Original catalogue requires explicit --case selection or a registered frozen cohort')
def prepare_selected(names):
    rows=[]
    for row in selected_rows(names):
        c,p=prepare_case(row)
        w,m,b,d=base.compile_coordinate_typed(p,c['typed_bindings'],probe_kind=c['catalogue_profile']['kind'],geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True)
        if c.get('declared_burst_sequence'):m['coordinate_original_input'].update(original_controls_preserved=False,declared_burst_sequence_applied_after_identity_check=True)
        if c.get('declared_manual_sequences'):m['coordinate_original_input'].update(original_controls_preserved=False,declared_manual_sequences_applied_after_identity_check=True)
        rows.append((c['name'],w,(c,m,b,d)))
    return rows,None

def native_reference(domain):
    from world_coordinate_typed_owner_native import observe
    from world_original_support_native import captures,capture
    if captures(domain[0]):
        with capture(domain[0]) as receipts:n,_=observe(domain[0])
        n['support_conditions']=receipts
    else:n,_=observe(domain[0])
    return verify(domain[0],n,skill_history_capacity=CAPACITY)

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    view,legacy,legacy_indices=compare_and_project(block,domain,n,indices)
    base.base.parent.parent.compare_observed(view,domain,legacy,legacy_indices)
    if domain[0]['catalogue_profile'].get('variant'):
        from portable_runtime import decode
        from portable_original_catalogue_cases import verify_role_casts
        verify_role_casts(domain[0],decode(block[:159744],domain[1])['burst_trace'])
    if 'support_conditions' in n:
        from portable_original_support_contracts import verify_gpu
        verify_gpu(block,domain,n)
    return n

def validate_rejection(block,name):raise AssertionError('Selected original profiles cannot be converted into expected rejections')
