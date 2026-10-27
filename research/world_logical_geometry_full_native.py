"""Logical colliders under the existing complete battle observation chain.

No new battle comparer, sampler or effect observer is installed. Device suite
admission remains separate until the logical scratch/wire checks are complete.
"""
import copy,importlib.util
from pathlib import Path
from coordinate_logical_actor_geometry import logical_actor_geometry
from portable_coordinate_original_cases import prepare_case as original_case
from portable_logical_geometry_wire import compile_logical_geometry

def prepare_case(row):
    case,prepared=original_case(row)
    case['logical_geometry']=copy.deepcopy(row['logical_geometry'])
    case['logical_geometry_contract']=copy.deepcopy(row['contract'])
    words,meta,bindings,scene=compile_logical_geometry(prepared,case['logical_geometry'])
    return words,(case,meta,bindings,scene)

def observe(domain):
    path=Path(__file__).with_name('verify-coordinate-original-short.py')
    spec=importlib.util.spec_from_file_location('logical_geometry_full_original',path)
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
    with logical_actor_geometry(domain[0]['logical_geometry']) as geometry:
        native=original.native_reference(domain)
    native['logical_geometry']=dict(shots=geometry['shots'],packets=geometry['packets'],pellets=geometry['pellets'])
    return native
