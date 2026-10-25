"""Original forced slots and expiry changes use existing shared handlers."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('original_source_cleanse',ROOT/'research/verify-coordinate-original-cleanse-short.py');cleanse=importlib.util.module_from_spec(spec);spec.loader.exec_module(cleanse)
parent=cleanse.parent;resources=cleanse.resources;stacks=cleanse.stacks
from portable_coordinate_original_source_cases import fixtures
from portable_coordinate_original_cases import prepare_case
from world_original_source_native import capture
from world_original_resource_native import capture as capture_resources
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_slot_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        case,prepared=prepare_case(row);case['source_witness']=row['source_witness'];words,metadata,bindings,desc=compile_coordinate_battle(prepared);rows.append((case['name'],words,(case,metadata,bindings,desc)))
    packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    with capture(domain[0]) as observed,capture_resources(domain[0]) as gauges:native=parent.native_reference(domain)
    native.update(original_source=observed,original_resources=gauges);verify_witness(domain[0],native);return native

def verify_witness(case,native):
    observed=native['original_source'];events=observed['dispatches'];forced=[e for e in events if e['stat']=='force_skill_use'];extended=[e for e in events if e['stat']=='named_buff_duration_extend']
    assert len(forced)==1 and forced[0]['time']==0 and forced[0]['actual_activations'],'Actual original initial forced slot required'
    label=case['source_witness'];expected=1 if label=='Julia-1' else 3 if label.startswith('Julia') else 2
    assert len(forced[0]['actual_activations'])==expected
    slot=case['effects'][forced[0]['row']]['target_skill']
    assert all(e['source']==slot and e['owner']==0 and e['time']==0 for e in forced[0]['actual_activations'])
    assert forced[0]['before_clocks']==forced[0]['after_clocks'],'Force must not reset periodic grid; an empty initial grid is not a nonempty-clock witness'
    if label!='Sakura-parts':
        assert not extended
        if label=='Sakura-control':assert not any(r['row']==5 and r['created']>=15 for r in native['skill_trace'])
    else:
        assert len(extended)==2 and [e['row'] for e in extended]==[2,3]
        deaths=[e for e in native['battle']['boss_log'] if e['event']=='destroy'];assert len(deaths)==1 and all(deaths[0]['time']<e['time'] for e in extended)
        for event,source in zip(extended,(4,5),strict=True):
            before=next(r for r in event['before'] if r['row']==source);after=next(r for r in event['after'] if r['row']==source)
            assert before['end']==15 and after['end']==before['end']+10.02 and before['activated']==after['activated']==0
            assert event['before_clocks'] and event['before_clocks']==event['after_clocks'],'Actual nonempty clock grid must remain unchanged'
            if source==5:assert before['dot']['next']==after['dot']['next'] and after['dot']['expiry']==after['end']
        assert any(r['row']==5 and r['created']>=15 for r in native['skill_trace']),'Extended DoT must deal real damage after the old expiry'
        assert any(r['row']==5 and r['dot']['expiry']==25.02 for r in observed['final'])
    if label.startswith('Sakura'):
        cast=next(r['created'] for r in native['skill_trace'] if r['row']==6)
        effect=case['effects'][7];post=cast+10*effect['ramp_interval']+effect['post_ramp_tick_delay']
        ramp=[r for r in native['skill_trace'] if r['row']==7 and r['created']<post]
        assert len(ramp)==10 and cast+effect['ramp_interval']<=ramp[0]['created']<=cast+effect['ramp_interval']+1/60,'All original ramp damage ticks must execute on the actual frame grid'
    return True

def compare_source_state(block,domain,native):
    from portable_runtime import decode
    actual=decode(block[:159744],domain[1]);case=domain[0];observed=native['original_source'];selected=set(observed['selected_rows'])
    for index,source in enumerate(domain[1]['binding_source_indices']):
        if case['effects'][source].get('stat') in ('force_skill_use','named_buff_duration_extend'):assert actual['timers'][index]['activations']==sum(e['row']==source for e in observed['dispatches']),'Each actual source operation must execute'
    expected=[{k:r[k] for k in ('row','owner','members','stack','activated','end')} for r in observed['final'] if r['end'] is None or r['end']>case['duration']];found=[]
    for index,carrier in enumerate(actual['carriers']):
        source=domain[1]['binding_source_indices'][carrier['definition']]
        if source not in selected or not carrier['active']:continue
        assert not carrier['lazy_pending'] and carrier['recipients']<64,'Selected original carriers contain allies or BODY only'
        members=[name for who,name in enumerate(case['names']) if carrier['recipients']&(1<<who)]
        root=bool(carrier['recipients']&32)
        # Wide DoT membership belongs to its captured actor tuple, not the
        # scalar allied mask. These original worlds have BODY and PART only.
        from portable_specs import LIMITS
        definition=carrier['definition'];periodic=LIMITS['WORLD_PERIODIC_DEFINITION_BASE']+definition*38
        if case['effects'][source].get('type')=='damage' and case['effects'][source].get('tick_interval'):
            count=block[periodic];assert count<=1 and (count==0 or block[periodic+2]==1),'Selected original DoT must retain only BODY'
            root=root or count==1
        if root:members.append('__enemy__')
        found.append(dict(row=source,owner=case['owners'][source],members=members,stack=carrier['stacks'],activated=carrier['activated'],end=stacks.stack_expiry(block,index)))
    key=lambda row:(row['row'],str(row['members']))
    assert sorted(found,key=key)==sorted(expected,key=key),'Every selected original final carrier and exact expiry must match'
    bindings={source:index for index,source in enumerate(domain[1]['binding_source_indices'])}
    for row in observed['final_clocks']:
        timer=actual['timers'][bindings[row['row']]];assert (timer['every_due'],timer['every_interval'])==(row['due'],row['interval']),'Original periodic grids must match'
    for row in observed['final']:
        if row['dot']:
            timer=actual['timers'][bindings[row['row']]];assert (timer['due'],timer['expiry'])==(row['dot']['next'],row['dot']['expiry']),'DoT next tick and expiry must match without phase reset'
    return native

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:native=native_reference(domain)
    parent.compare_observed(block,domain,native,indices);resources.compare_resource_state(block,domain,native)
    return compare_source_state(block,domain,native)

def validate_rejection(block,name):raise AssertionError('Original source definitions cannot be discarded')
