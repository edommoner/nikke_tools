"""Shared original gauge charge/consume, final quantities and actual dispatches."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('resource_original_parent',ROOT/'research/verify-coordinate-original-short.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
from portable_coordinate_original_resource_cases import fixtures
from portable_coordinate_original_cases import prepare_case
from world_original_resource_native import capture
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_resource_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        case,prepared=prepare_case(row);case['resource_witness']=row['resource_witness'];words,metadata,bindings,desc=compile_coordinate_battle(prepared);rows.append((case['name'],words,(case,metadata,bindings,desc)))
    packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    with capture(domain[0]) as resources:native=parent.native_reference(domain)
    native['original_resources']=resources;verify_witness(domain[0],native);return native

def verify_witness(case,native):
    observed=native['original_resources'];events=observed['dispatches'];owner=case['names'][0];final=observed['final'][owner]
    assert any(e['stat']=='gauge_charge' for e in events) and any(e['stat']=='gauge_consume' for e in events)
    if case['resource_witness'].startswith('EH'):
        expected=4 if case['resource_witness']=='EH-cap' else 1
        assert final['사제 탄창']==expected and final['폐품']==(10 if expected==4 else 0)
        assert final['_gauge_max:사제 탄창']==4 and final['_gauge_max:폐품']==10
        if expected==4:
            assert len([r for r in native['battle']['boss_log'] if r['event']=='destroy'])==24
            assert any(r['stat']=='gauge_charge' and r['resource']=='폐품' and r['before'].get(owner,{}).get('폐품')==r['after'][owner]['폐품']==10 for r in events),'Actual cap-clipped charge required'
        else:assert len(events)==3
    else:
        assert final['화력 게이지']==0 and final['_gauge_max:화력 게이지']==100
        spent=[r for r in events if r['stat']=='gauge_consume'];assert len(spent)==1 and spent[0]['time']>0
        assert spent[0]['before'][owner]['화력 게이지']==100 and spent[0]['after'][owner]['화력 게이지']==0
    return True

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:native=native_reference(domain)
    parent.compare_observed(block,domain,native,indices)
    return compare_resource_state(block,domain,native)

def compare_resource_state(block,domain,native):
    from portable_runtime import decode
    actual=decode(block[:159744],domain[1]);observed=native['original_resources'];names=domain[1]['resource_names']
    for who,owner in enumerate(domain[0]['names']):
        state=observed['final'].get(owner,{})
        assert {key for key in state if not key.startswith('_gauge_max:')}<=set(names),'Every actual gauge requires a wire identity'
        for key in names:
            cap='_gauge_max:'+key
            assert actual['resources'][who][key]==dict(present=key in state,value=state.get(key,0),cap_present=cap in state,base_cap=state.get(cap)),'Stored gauge value, presence and base cap must match'
    expected=[dict(event=30,**r) for r in observed['notifications']]
    assert actual['resource_trace']==expected and actual['resource_trace_total']==len(expected),'Every actual step notification, including zero spurious notifications'
    for index,source in enumerate(domain[1]['binding_source_indices']):
        if domain[0]['effects'][source].get('stat') in ('gauge_charge','gauge_consume'):assert actual['timers'][index]['activations']==sum(r['row']==source for r in observed['dispatches']),'Each actual original gauge dispatch must execute'
    return native

def validate_rejection(block,name):raise AssertionError('Original resource definitions cannot be discarded')
