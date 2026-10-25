"""Real original random/allied cleanse and enemy-world dispel share one entry."""
import array,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('original_cleanse_stacks',ROOT/'research/verify-coordinate-original-stacks-short.py');stacks=importlib.util.module_from_spec(spec);spec.loader.exec_module(stacks)
parent=stacks.parent;resources=stacks.resources
from portable_coordinate_original_cleanse_cases import fixtures
from portable_coordinate_original_cases import prepare_case
from world_original_cleanse_native import capture
from world_original_resource_native import capture as capture_resources
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_cleanse_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        case,prepared=prepare_case(row);case.update(cleanse_witness=row['cleanse_witness'],observe_overlay=True,observe_cleanse=True)
        words,metadata,bindings,desc=compile_coordinate_battle(prepared);rows.append((case['name'],words,(case,metadata,bindings,desc)))
    packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    with capture(domain[0]) as cleanse,capture_resources(domain[0]) as gauges:native=parent.native_reference(domain)
    native.update(original_cleanse=cleanse,original_resources=gauges);verify_witness(domain[0],native);return native

def verify_witness(case,native):
    observed=native['original_cleanse'];events=observed['dispatches'];assert events,'Original cleanse must actually execute'
    label=case['cleanse_witness']
    if label=='Cocoa-empty':assert len(events)==1 and events[0]['before']==events[0]['after']==[]
    elif label=='Cocoa-partial':
        assert len(events)==2 and len(events[-1]['before'])==len(events[-1]['after'])==1
        before,after=events[-1]['before'][0],events[-1]['after'][0]
        assert before['members']==case['names'] and after['members']==[case['names'][i] for i in (0,3,4)]
        assert before['row']==after['row'] and before['stack']==after['stack']==1 and before['end'] is after['end'] is None
        assert any(d['kind']=='native-bits' for d in native['sampled_draws']),'Actual random-recipient integer RNG receipt required'
        assert observed['final']==events[-1]['after']
    elif label=='Mica-all':
        assert len(events)==2 and events[-1]['before'][0]['members']==case['names'] and events[-1]['after']==[] and observed['final']==[]
    elif label=='Rosanna-overlays':
        assert len(events)==1 and events[0]['stat']=='enemy_buff_cleanse'
        assert [r['dispelled'] for r in native['battle']['world_nodes']]==[False,True,False,True]
        assert [r['pattern'] for r in native['battle']['boss_log'] if r['event']=='dispel']==['ordinary-b','ordinary-a']
    else:raise AssertionError('Unknown original cleanse witness')
    return True

def compare_cleanse_state(block,domain,native):
    from portable_runtime import decode
    from portable_specs import LIMITS as L
    from portable_coordinate_sampling_bank import LAYOUT as BANK
    assert list(block[L['REVIVAL_RNG_BASE']:L['REVIVAL_RNG_BASE']+BANK['RNG_WORDS']])==list(block[BANK['RNG']:BANK['RNG']+BANK['RNG_WORDS']]),'Exported recipient RNG must be the exact shared sampled MT state'
    actual=decode(block[:159744],domain[1]);case=domain[0];observed=native['original_cleanse']
    for index,source in enumerate(domain[1]['binding_source_indices']):
        if case['effects'][source].get('stat') in ('debuff_cleanse','enemy_buff_cleanse'):assert actual['timers'][index]['activations']==sum(r['row']==source for r in observed['dispatches']),'Every original cleanse dispatch must execute'
    found=[]
    for index,carrier in enumerate(actual['carriers']):
        source=domain[1]['binding_source_indices'][carrier['definition']];effect=case['effects'][source]
        if not carrier['active'] or not effect.get('polarity','').startswith('harmful'):continue
        assert carrier['recipients']<32,'Selected original harmful carriers are allied'
        found.append(dict(row=source,owner=case['owners'][source],members=None if carrier['lazy_pending'] else [name for i,name in enumerate(case['names']) if carrier['recipients']&(1<<i)],stack=carrier['stacks'],activated=carrier['activated'],end=stacks.stack_expiry(block,index)))
    expected=[r for r in observed['final'] if r['end'] is None or r['end']>case['duration']];key=lambda row:(row['row'],str(row['members']))
    assert sorted(found,key=key)==sorted(expected,key=key),'Every surviving harmful carrier and unselected ally must match'
    from world_overlay_node_readback import read_nodes
    nodes=read_nodes(block,len(case['patterns']),cleanse=True)
    assert nodes==native['battle']['world_nodes'],'Actual enemy-world dispels and irremovable nodes must match'
    return native

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:native=native_reference(domain)
    parent.compare_observed(block,domain,native,indices);resources.compare_resource_state(block,domain,native)
    return compare_cleanse_state(block,domain,native)

def validate_rejection(block,name):raise AssertionError('Original cleanse definitions cannot be discarded')
