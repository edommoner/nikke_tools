"""Original harmful-stack removal reuses existing stack and resource observers."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('original_harmful_stack_parent',ROOT/'research/verify-coordinate-original-stacks-short.py');stacks=importlib.util.module_from_spec(s);s.loader.exec_module(stacks);parent=stacks.parent;resources=stacks.resources
from portable_coordinate_original_cases import prepare_case
from portable_coordinate_original_harmful_stack_cases import fixtures
from world_original_stack_native import capture
from world_original_resource_native import capture as capture_resources
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_shared_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle
def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);c['harmful_stack_witness']=row['harmful_stack_witness'];c['python_observers_only']=True;c['coordinate_packet_history']='ordered-sha256-v1';w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def verify_witness(case,native):
    o=native['original_harmful_stacks'];events=o['dispatches']
    if case['harmful_stack_witness']=='control':
        assert not events and len(o['final'])==1 and o['final'][0]['stack']==1
    else:
        assert len(events)==1 and events[0]['stat']=='debuff_stack_remove'
        event=events[0];assert case['effects'][event['row']]['stat']=='debuff_stack_remove' and case['names'][event['owner']]=='앵커 : 이노센트 메이드'
        assert len(event['before'])==len(event['after'])==1
        before,after=event['before'][0],event['after'][0];effect=case['effects'][before['row']]
        assert effect['name']=='취기' and effect['polarity']=='harmful' and effect['max_stack']==3
        assert before['stack']==3 and after['stack']==2
        assert {k:v for k,v in before.items() if k!='stack'}=={k:v for k,v in after.items() if k!='stack'},'Decrement must preserve actual membership, activation and expiration'
        assert before['end'] is None and event['partial_skips_before']==event['partial_skips_after']==0
        assert o['final']==event['after']
        notices=[n for n in o['notifications'] if n['event'].startswith('stack_reach:취기:')]
        assert [n['event'] for n in notices]==['stack_reach:취기:'+str(i) for i in (1,2,3)]
        assert notices[-1]['time']<=event['time'],'Third burst must first create the third harmful stack'
    return True
def native_reference(domain):
    with capture(domain[0]) as observed,capture_resources(domain[0]) as gauges:n=parent.native_reference(domain)
    n.update(original_harmful_stacks=observed,original_resources=gauges);verify_witness(domain[0],n);return n
def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices);resources.compare_resource_state(block,domain,n)
    return stacks.compare_stack_state(block,domain,n,operations=('debuff_stack_remove',),field='original_harmful_stacks')
def validate_rejection(block,name):raise AssertionError('Original harmful stack definitions cannot be discarded')
