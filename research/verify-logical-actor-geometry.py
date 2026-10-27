"""Full original battles and common comparers for declared logical colliders."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
base=module('logical_actor_original_base','research/verify-coordinate-original-short.py')
groups=module('logical_actor_group_base','research/verify-coordinate-group-short.py')
from portable_logical_geometry_cases import fixtures
from world_logical_geometry_full_native import prepare_case,observe
from portable_skill_history import compare_and_project
SOURCE='gpu/world_coordinate_logical_actor_entry.slang'
suite=SimpleNamespace(INPUT=115680,OUTPUT=2032000);cross=base.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT

def prepare():
    rows=[]
    for case in fixtures():
        words,domain=prepare_case(case);rows.append((case['name'],words,domain))
    seed=rows[0][1]
    for label,offset,value in [('magic',0,0),('version',1,2),('reserved',4,1),('body-binding',32,0),('kind',33,1),('map',4097,0),('nonfinite-shape',41,0x7ff00000)]:
        words=list(seed);words[109968+offset]=value;rows.append(('reject/logical-actor-geometry/'+label,words,None))
    raw=array.array('I',[len(rows)])
    for _,words,_ in rows:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    n=observe(domain);scenario=domain[0]['logical_geometry_contract']['scenario']
    assert n['original_input_identity']['definitions']==68
    assert n['original_input_identity']['chars_config_seed_weapon_verified']
    assert n['physical_pellets'] and n['sampled_points'] and n['logical_geometry']['shots']
    if scenario in ('three-enemies','one-outside','part-not-enemy'):
        assert not n['group_notices'] and not n['group_children'] and not n['group_child_landings']
        assert all(len(g['targets'])<=3 for g in n['groups'])
    else:
        assert n['group_notices'] and n['group_children'] and n['group_child_landings']
        assert all(len(g['targets'])==4 for g in n['groups'][:1])
    return n

def compare(block,domain):
    assert len(block)==suite.OUTPUT and block[0]==0,'Complete successful logical actor output required'
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    return compare_observed(block,domain,n,indices)

def compare_observed(block,domain,n,indices):
    assert len(block)==suite.OUTPUT and block[0]==0,'Complete successful logical actor output required'
    view,legacy,legacy_indices=compare_and_project(block,domain,n,indices)
    base.compare_observed(view[:1769856],domain,legacy,legacy_indices)
    groups.compare_group_receipts(view[:1507328],domain,n,compare_packets=False)
    assert not any(view[1769856:]),'Logical shot scratch and all unowned tail words must be released'
    return n

def validate_rejection(block,name):
    assert name.startswith('reject/logical-actor-geometry/') and block[0]==64,(name,block[0])
