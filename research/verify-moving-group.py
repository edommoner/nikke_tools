"""Original group effects and moving targets share the sealed physical entry."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('moving_group_common',ROOT/'research/verify-moving-typed.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
from portable_moving_group_cases import fixtures,prepare_case
from portable_moving_group_contracts import verify
from world_moving_group_native import observe
from portable_moving_typed_wire import compile_battle
SOURCE=base.SOURCE;STRICT_WIRE_DIMENSIONS=True;suite=base.suite
cross=base.cross;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT

def prepare():
    rows=[]
    for raw in fixtures():
        c,p=prepare_case(raw);words,meta,actors,scene=compile_battle(p,c)
        rows.append((c['name'],words,(c,meta,actors,scene)))
    rows.extend(row for row in base.prepare()[0] if row[2] is None)
    data=array.array('I',[len(rows)])
    for _,words,_ in rows:data.extend(words)
    if sys.byteorder!='little':data.byteswap()
    return rows,data.tobytes()

def native_reference(domain):
    n,_=observe(domain[0]);verify(domain[0],n)
    base.require_capacity(n);motion=n['enemy_movement']
    assert len(motion['frames'])<=4096 and sum(len(f['segments']) for f in motion['frames'])<=4096
    return n

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    return base.compare_observed(block,domain,n,indices)

validate_rejection=base.validate_rejection
