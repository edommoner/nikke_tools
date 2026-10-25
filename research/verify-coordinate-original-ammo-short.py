"""Existing shared ammo operations in complete sampled original battles."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('ammo_resource_parent',ROOT/'research/verify-coordinate-original-resources-short.py');resources=importlib.util.module_from_spec(spec);spec.loader.exec_module(resources)
parent=resources.parent
from portable_coordinate_original_ammo_cases import fixtures
from portable_coordinate_original_cases import prepare_case
from world_original_ammo_native import capture as capture_ammo
from world_original_resource_native import capture as capture_resources
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_ammo_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        case,prepared=prepare_case(row);case['ammo_witness']=row['ammo_witness'];words,metadata,bindings,desc=compile_coordinate_battle(prepared);rows.append((case['name'],words,(case,metadata,bindings,desc)))
    packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    with capture_ammo(domain[0]) as ammo,capture_resources(domain[0]) as gauges:native=parent.native_reference(domain)
    native.update(original_ammo=ammo,original_resources=gauges);verify_witness(domain[0],native);return native

def verify_witness(case,native):
    ammo=native['original_ammo'];assert ammo,'The original ammo handler must actually execute'
    for row in ammo:
        assert set(row['capacities'])=={str(owner) for owner in row['targets']}
        for who in row['targets']:
            capacity=row['capacities'][str(who)];before=row['before'][who]['ammo'];after=row['after'][who]['ammo']
            change=round(capacity*(row['value']/100.0)) if row['stat']=='ammo_charge_pct' else int(row['value'])
            expected=min(before+change,capacity)
            if row['stat']=='ammo_charge_pct':expected=max(0,expected)
            assert after==expected,'Read-only snapshots must attest native percentage rounding/flat conversion and clipping'
    label=case['ammo_witness']
    if label=='Guillotine-winter':
        steps=native['original_resources']['notifications'];assert steps and all(r['resource']=='경험치' and r['boundary']%10==0 for r in steps)
        assert len(ammo)==len(steps) and all(a['time']==s['time'] for a,s in zip(ammo,steps,strict=True))
        assert native['original_resources']['final'][case['names'][0]]['용사 레벨']==1+len(steps)
        assert any(r['after'][0]['ammo']>r['before'][0]['ammo'] for r in ammo),'Level rewards must really replenish bullets'
    elif label=='Noir':
        assert len(ammo)==1 and ammo[0]['targets']==list(range(5))
        assert any(ammo[0]['before'][i]['ammo']+round(ammo[0]['capacities'][str(i)]*(ammo[0]['value']/100.0))>ammo[0]['capacities'][str(i)] for i in range(5)),'Real upper-cap clipping required'
    elif label=='Arcana':
        assert len(ammo)>=2 and all(r['stat']=='ammo_charge_flat' for r in ammo)
        assert {r['value'] for r in ammo}=={2.0,6.0}
    elif label=='Grave-drain':
        assert len(ammo)==1 and ammo[0]['value']==-100 and ammo[0]['before'][0]['ammo']>0 and ammo[0]['after'][0]['ammo']==0
    else:raise AssertionError('Unknown original ammo witness')
    return True

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:native=native_reference(domain)
    parent.compare_observed(block,domain,native,indices)
    resources.compare_resource_state(block,domain,native)
    from portable_runtime import decode
    actual=decode(block[:159744],domain[1])
    for index,source in enumerate(domain[1]['binding_source_indices']):
        if domain[0]['effects'][source].get('stat') in ('ammo_charge_pct','ammo_charge_flat'):assert actual['timers'][index]['activations']==sum(r['row']==source for r in native['original_ammo']),'Each actual original ammo dispatch must execute'
    return native

def validate_rejection(block,name):raise AssertionError('Original ammo definitions cannot be discarded')
