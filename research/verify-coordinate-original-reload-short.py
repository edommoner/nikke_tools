"""Original forced reloads, using shared battle and reload comparison readers."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('original_reload_parent',ROOT/'research/verify-coordinate-original-short.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
from portable_coordinate_original_reload_cases import fixtures
from portable_coordinate_original_cases import prepare_case
from world_original_reload_native import capture
from portable_reload_observation import readback
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_reload_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);c['reload_witness']=row['reload_witness'];w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    with capture(domain[0]) as observed:n=parent.native_reference(domain)
    n['original_reload']=observed
    verify_witness(domain[0],n)
    return n

def verify_witness(case,native):
    result=native['original_reload'];requests=result['requests'];label=case['reload_witness']
    if label=='Milk-auto':assert not requests,'Fully automatic control must retain its actual no-force behavior'
    else:
        assert requests and any(r['starts'] for r in requests),'Original force request must actually start a reload'
        for r in requests:
            assert r['owner']==0 and case['effects'][r['row']]['stat']=='force_reload' and case['effects'][r['row']]['target']=='self'
            before,after=r['before'],r['after'];assert before[1:]==after[1:],'Original self request must preserve other actors'
            if before[0]['until']>0:assert not r['starts'] and before==after,'An already reloading actor must be unchanged'
            else:assert len(r['starts'])==1 and r['starts'][0]['owner']==0 and after[0]['ammo']==0 and after[0]['until']>r['time'],'Actual force must enter the original reload lifecycle'
    return True

def compare_reload(block,domain,native):
    actual=readback(block,domain[1]);observed=native['original_reload']
    assert actual['reload_events']==observed['events'],'Every original forced/start/finish reload call must match'
    assert actual['reload_until']==[r['until'] for r in observed['final']],'All final reload clocks must match'
    from portable_runtime import decode
    from portable_specs import LIMITS as L
    import struct
    # These original idle worlds land every full-charge shot on BODY. Their
    # actual full-charge receipts therefore also witness the last-fire clock.
    for who,control in enumerate(domain[0]['controls']):
        if not control.get('tap_fire') and not any(e.get('mode')=='tap' for e in control.get('click',[])):continue
        at=L['WORLD_CONTROL_STATE_BASE']+who*32;times=[r['time'] for r in native['full_charge_quantities'] if r['owner']==who]
        assert block[at+23]==bool(times),'Only actual full shots own periodic full-charge history'
        if times:assert struct.unpack('<d',struct.pack('<II',*block[at+30:at+32]))[0]==times[-1],'An interrupted charge cannot advance the last-full-shot clock'
    timers=decode(block[:159744],domain[1])['timers']
    for index,source in enumerate(domain[1]['binding_source_indices']):
        if domain[0]['effects'][source].get('stat')=='force_reload':assert timers[index]['activations']==sum(r['row']==source for r in observed['requests']),'Each actual original request must be counted'
    return native

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices)
    return compare_reload(block,domain,n)

def validate_rejection(block,name):raise AssertionError('Original reload definitions cannot be discarded')
