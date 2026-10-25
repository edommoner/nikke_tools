"""Original stack initialization and later spending under the fixed shared source."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('original_init_stacks',ROOT/'research/verify-coordinate-original-stacks-short.py');stacks=importlib.util.module_from_spec(s);s.loader.exec_module(stacks);parent=stacks.parent
from portable_coordinate_original_cases import prepare_case
from portable_coordinate_original_init_cases import fixtures
from world_original_stack_native import capture
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_shared_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);c['init_level']=row['init_level'];w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def verify_witness(case,native):
    observed=native['original_stacks'];events=observed['dispatches'];initial={1:40,4:45,10:50}[case['init_level']]
    assert len(events)==2 and [e['stat'] for e in events]==['buff_stack_init','buff_stack_remove']
    first,last=events;assert first['time']==0 and first['before']==[] and len(first['after'])==1
    carrier=first['after'][0];assert carrier==dict(row=1,owner=0,members=[case['names'][0]],stack=initial,activated=0.,end=None)
    assert last['time']>first['time'] and last['before'][0]['stack']==initial and last['after'][0]['stack']==initial-17
    assert last['after'][0]['end'] is None and last['after'][0]['activated']==0.
    final=observed['final'];assert len(final)==1 and final[0]['stack']==initial-14 and final[0]['end'] is None
    assert final[0]['activated']>last['time']
    name=case['effects'][1]['name'];reached=[n for n in observed['notifications'] if n['event'].startswith('stack_reach:'+name+':')]
    assert [n['event'] for n in reached]==['stack_reach:'+name+':'+str(initial-17+i) for i in (1,2,3)]
    assert all(n['time']>last['time'] for n in reached),'Initialization does not synthesize a stack-reach notification'
    assert all(e['partial_skips_before']==e['partial_skips_after']==0 for e in events)
    return True

def native_reference(domain):
    with capture(domain[0]) as observed:n=parent.native_reference(domain)
    n['original_stacks']=observed;verify_witness(domain[0],n);return n

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices)
    return stacks.compare_stack_state(block,domain,n,operations=('buff_stack_init','buff_stack_remove'))

def validate_rejection(block,name):raise AssertionError('Original stack initialization definitions cannot be discarded')
