"""Original enemy stack mutations reuse source carrier/clock and resource readers."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('original_enemy_stack_source',ROOT/'research/verify-coordinate-original-source-short.py');source=importlib.util.module_from_spec(s);s.loader.exec_module(source);parent=source.parent;resources=source.resources
from portable_coordinate_original_cases import prepare_case
from portable_coordinate_original_enemy_stack_cases import fixtures
from world_original_stack_native import capture
from world_original_resource_native import capture as capture_resources
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_shared_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle
def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);c['enemy_stack_witness']=row['enemy_stack_witness'];w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def verify_witness(case,native):
    o=native['original_enemy_stacks'];events=o['dispatches'];label=case['enemy_stack_witness']
    if label=='control':
        assert not events and len(o['final'])==1
        assert case['effects'][o['final'][0]['row']]['name']=='사슬 감기' and o['final'][0]['stack']==10
        assert o['final'][0]['end'] is None and o['final'][0]['dot'],'Pre-burst control preserves the original ten-stack DoT'
    elif label=='transfer':
        assert len(o['final'])==1
        assert case['effects'][o['final'][0]['row']]['name']=='사슬 당기기','Original burst transfers the stack to its finite DoT'
        assert o['final'][0]['dot'] and o['final'][0]['end'] is not None
    else:
        assert events and all(e['stat']=='debuff_stack_add' for e in events)
        for event in events:
            assert len(event['before'])==len(event['after'])==1
            before,after=event['before'][0],event['after'][0]
            assert case['effects'][before['row']]['name']=='사슬 감기' and before['members']==['__enemy__']
            assert before['end'] is after['end'] is None and before['activated']==after['activated']==0.
            assert before['dot']==after['dot'],'Stack mutation must not reset the actual DoT tick grid'
            assert event['partial_skips_before']==event['partial_skips_after']==0
            expected=min(20,before['stack']+(1 if label=='hits' else 20));assert after['stack']==expected
        assert len(o['final'])==1 and o['final'][0]['stack']==20
        if label=='hits':
            assert len(events)>=11 and events[0]['before'][0]['stack']==10
            assert events[-1]['before'][0]['stack']==events[-1]['after'][0]['stack']==20,'Actual shot-triggered operation must also run at cap'
        else:
            assert len(events)==1 and events[0]['before'][0]['stack']==10
            assert len(native['battle']['hits'])==1 and native['battle']['hits'][0]['time']<=events[0]['time']
    return True

def native_reference(domain):
    c=domain[0];selected={i for i,e in enumerate(c['effects']) if e.get('stat')=='dot_damage'}
    with capture(c,selected_rows=selected) as observed,capture_resources(c) as gauges:n=parent.native_reference(domain)
    n.update(original_enemy_stacks=observed,original_resources=gauges);verify_witness(c,n);return n

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices);resources.compare_resource_state(block,domain,n)
    return source.compare_source_state(block,domain,n,field='original_enemy_stacks',operations=('debuff_stack_add',))
def validate_rejection(block,name):raise AssertionError('Original enemy-stack definitions cannot be discarded')
