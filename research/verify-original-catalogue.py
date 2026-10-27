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

def case_catalog():return list(catalog())
def prepare():raise ValueError('Original catalogue requires explicit --case selection or a registered frozen cohort')
def prepare_selected(names):
    rows=[]
    for row in selected_rows(names):
        c,p=prepare_case(row)
        w,m,b,d=base.compile_coordinate_typed(p,c['typed_bindings'],probe_kind=c['catalogue_profile']['kind'],geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True,coordinate_typed_owners=True)
        rows.append((c['name'],w,(c,m,b,d)))
    return rows,None

def native_reference(domain):
    from world_coordinate_typed_owner_native import observe
    n,_=observe(domain[0]);return verify(domain[0],n,skill_history_capacity=CAPACITY)

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    view,legacy,legacy_indices=compare_and_project(block,domain,n,indices)
    base.base.parent.parent.compare_observed(view,domain,legacy,legacy_indices)
    return n

def validate_rejection(block,name):raise AssertionError('Selected original profiles cannot be converted into expected rejections')
