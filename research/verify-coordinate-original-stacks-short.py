"""Original own-stack changes and current-stack rewards in shared battles."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('original_stack_resources',ROOT/'research/verify-coordinate-original-resources-short.py');resources=importlib.util.module_from_spec(spec);spec.loader.exec_module(resources)
parent=resources.parent
from portable_coordinate_original_stack_cases import fixtures
from portable_coordinate_original_cases import prepare_case
from world_original_stack_native import capture
from world_original_resource_native import capture as capture_resources
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_stack_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        case,prepared=prepare_case(row);case['stack_witness']=row['stack_witness'];words,metadata,bindings,desc=compile_coordinate_battle(prepared);rows.append((case['name'],words,(case,metadata,bindings,desc)))
    packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    with capture(domain[0]) as stacks,capture_resources(domain[0]) as gauges:native=parent.native_reference(domain)
    native.update(original_stacks=stacks,original_resources=gauges);verify_witness(domain[0],native);return native

def verify_witness(case,native):
    observed=native['original_stacks'];events=observed['dispatches'];assert events,'Original stack operation must execute'
    label=case['stack_witness']
    if label=='Pepper-no-carrier':
        assert len(events)==1 and events[0]['stat']=='buff_max_stack_add' and events[0]['before']==events[0]['after']==[]
    elif label=='Rupee':
        assert len(events)==1 and events[0]['stat']=='buff_max_stack_add'
        before,after=events[0]['before'][0],events[0]['after'][0]
        assert before['stack']==3 and after['stack']==4 and after['activated']==events[0]['time'] and after['end']==events[0]['time']+15
        assert observed['final'][0]['stack']==5
        assert any(n['time']==events[0]['time'] and n['event'].endswith(':4') for n in observed['notifications'])
    elif label.startswith('Marine-'):
        assert events[0]['stat']=='buff_stack_add' and events[0]['before'][0]['stack']==1 and events[0]['after'][0]['stack']==5
        assert all(row['end'] is None for e in events for row in e['after'])
        if label=='Marine-cap':
            assert len(events)==2 and events[-1]['before'][0]['stack']==events[-1]['after'][0]['stack']==5
        else:
            assert [e['before'][0]['stack']-e['after'][0]['stack'] for e in events if e['stat']=='buff_stack_remove']==[1,1,1]
            assert events[-1]['stat']=='buff_stack_add' and events[-1]['before'][0]['stack']==2 and events[-1]['after'][0]['stack']==3
    else:raise AssertionError('Unknown original stack witness')
    return True

def stack_expiry(block,index):
    # The legacy display decoder maps infinity to finite 1e30. Preserve the
    # actual wire distinction for an exact comparison with native None.
    import struct
    from portable_specs import LIMITS as L
    at=L['CARRIER_STATE_BASE']+index*L['CARRIER_WORDS']+5
    pair=block[at:at+2]
    return None if tuple(pair)==(0,0x7ff00000) else struct.unpack('<d',struct.pack('<II',*pair))[0]

def compare_stack_state(block,domain,native,*,operations=('buff_stack_add','buff_stack_remove','buff_max_stack_add'),field='original_stacks'):
    from portable_runtime import decode
    actual=decode(block[:159744],domain[1]);case=domain[0];observed=native[field]
    for index,source in enumerate(domain[1]['binding_source_indices']):
        if case['effects'][source].get('stat') in operations and case['effects'][source].get('type') in ('buff','instant'):
            assert actual['timers'][index]['activations']==sum(r['row']==source for r in observed['dispatches']),'Every original stack operation must execute'
    expected=[row for row in observed['final'] if row['end'] is None or row['end']>case['duration']]
    found=[]
    for index,carrier in enumerate(actual['carriers']):
        source=domain[1]['binding_source_indices'][carrier['definition']];effect=case['effects'][source]
        if not carrier['active'] or effect.get('type')!='buff' or effect.get('max_stack',1)==1:continue
        assert carrier['recipients']<32,'Selected original stack witnesses have allied carriers only'
        found.append(dict(row=source,owner=case['owners'][source],members=None if carrier['lazy_pending'] else [name for i,name in enumerate(case['names']) if carrier['recipients']&(1<<i)],stack=carrier['stacks'],activated=carrier['activated'],end=stack_expiry(block,index)))
    key=lambda row:(row['row'],str(row['members']))
    assert sorted(found,key=key)==sorted(expected,key=key),'All final original stack carriers, lifetime and membership must match'
    return native

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:native=native_reference(domain)
    parent.compare_observed(block,domain,native,indices);resources.compare_resource_state(block,domain,native)
    return compare_stack_state(block,domain,native)

def validate_rejection(block,name):raise AssertionError('Original stack definitions cannot be discarded')
