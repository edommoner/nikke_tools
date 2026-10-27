"""Further original roster coverage using the same logical actor executor."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('logical_rosters_common_comparison',ROOT/'research/verify-logical-actor-geometry.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_logical_geometry_roster_cases import fixtures
from portable_logical_geometry_roster_contracts import verify
from world_logical_geometry_full_native import prepare_case,observe
from portable_skill_history import require_capacity
SOURCE=base.SOURCE;suite=base.suite;cross=base.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT

def prepare():
    rows=[]
    for case in fixtures():
        words,domain=prepare_case(case);rows.append((case['name'],words,domain))
    raw=array.array('I',[len(rows)])
    for _,words,_ in rows:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    n=observe(domain);verify(domain[0],n);require_capacity(n);return n

def compare(block,domain):
    assert len(block)==suite.OUTPUT and block[0]==0,'Complete successful original logical actor output required'
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    return base.compare_observed(block,domain,n,indices)

def validate_rejection(block,name):raise AssertionError('Original roster cases cannot become expected rejections')
