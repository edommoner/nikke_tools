"""Complete original rosters through existing shared execution and comparators."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('original_coordinate_parent',ROOT/'research/verify-coordinate-healing-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_original_cases import fixtures,prepare_case
from portable_coordinate_roster_input import compile_coordinate_battle,SOURCE,INPUT_WORDS,OUTPUT_WORDS
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS);STRICT_WIRE_DIMENSIONS=True;cross=parent.cross
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def native_reference(domain):
    n=parent.native_reference(domain);n['original_input_identity']=n['battle'].pop('original_input_identity');return n
def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices)
    burst=parent.parent.parent.parent
    if Path(burst.__file__).name!='verify-coordinate-burst-control-short.py':raise ValueError('Original control comparator chain changed')
    mode=burst.parent;squad=mode.parent;policy=squad.parent
    burst.compare_state(block,n);mode.compare_state(block,n)
    clean=list(block);h=mode.STATE_BASE;clean[h+1]=1;clean[h+5]=0;clean[h+16:]=[0]*(len(clean)-h-16)
    squad.compare_state(clean,n,0)
    clean[squad.SQUAD_BASE:]=[0]*(len(clean)-squad.SQUAD_BASE)
    policy.compare_policy_state(clean,n,domain[1]['coordinate_original_input']['policy_mask'])
    return n
def validate_rejection(block,name):raise AssertionError('No original definition may be discarded as a rejection')
