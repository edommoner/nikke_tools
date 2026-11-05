"""Original shield healing through unchanged common protection and battle readers."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
parent=module('original_shield_parent','research/verify-coordinate-original-short.py')
stacks=module('original_shield_expiry','research/verify-coordinate-original-stacks-short.py')
from portable_coordinate_original_shield_cases import fixtures
from portable_coordinate_original_cases import prepare_case
from world_original_shield_native import capture
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_shield_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);c['shield_witness']=row['shield_witness'];c['python_observers_only']=True;w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    with capture(domain[0]) as observed:n=parent.native_reference(domain)
    n['original_shield']=observed
    verify_witness(domain[0],n)
    return n

def verify_witness(case,native):
    observed=native['original_shield'];scenario=case['shield_witness']['scenario'];deliveries=observed['deliveries']
    assert all(case['effects'][r['row']]['stat']=='shield_heal_pct' and r['owner']==0 for r in observed['requests'])
    if scenario=='full':assert deliveries and all(d['healed']==0 and d['before']==d['after'] for d in deliveries),'Actual full-shield requests must preserve capacity'
    elif scenario=='chipped':
        healed=[d for d in deliveries if d['healed']>0];assert healed,'A real hit must create room for actual healing'
        assert len(native['battle']['hits'])==2 and any(d['time']<native['battle']['hits'][-1]['time'] for d in healed),'A real later hit must expose restored protection before the capture ends'
    else:assert any(h['shield']>0 for h in native['battle']['hits']),'Broken-shield world must absorb real damage'
    for event in deliveries:
        assert event['amount']>=event['healed']>=0 and event['target']==0
        assert [(r['row'],r['capacity']) for r in event['before']]==[(r['row'],r['capacity']) for r in event['after']],'Healing cannot create a protection object or change capacity'
    return True

def compare_protections(block,domain,native,*,kind=1,stat='shield_heal_pct',field='original_shield'):
    from portable_runtime import decode
    c,m,_,_=domain;actual=decode(block[:159744],m);found=[]
    for index,carrier in enumerate(actual['carriers']):
        protection=carrier.get('protection',{})
        if not carrier['active'] or protection.get('kind')!=kind:continue
        source=m['binding_source_indices'][carrier['definition']];assert carrier['recipients']<32 and not carrier['lazy_pending']
        found.append(dict(row=source,owner=c['owners'][source],members=[name for who,name in enumerate(c['names']) if carrier['recipients']&(1<<who)],stack=carrier['stacks'],activated=carrier['activated'],end=stacks.stack_expiry(block,index),current={c['names'][int(w)]:v for w,v in protection['current'].items()},capacity={c['names'][int(w)]:v for w,v in protection['capacity'].items()}))
    key=lambda r:(r['row'],r['owner'],str(r['members']))
    assert sorted(found,key=key)==sorted(native[field]['final'],key=key),'All original final shield objects, exact quantities and expiration must match'
    for index,source in enumerate(m['binding_source_indices']):
        if c['effects'][source].get('stat')==stat:
            assert actual['timers'][index]['activations']==sum(r['row']==source and not r['from_tick'] for r in native[field]['requests']),'Every actual original heal request must execute'
    from portable_specs import LIMITS as L
    import struct
    bindings={source:index for index,source in enumerate(m['binding_source_indices'])}
    for clock in native[field]['clocks']:
        row=bindings[clock['row']];timer=actual['timers'][row];at=L['STATE_BASE']+row*10+2
        expiry=None if tuple(block[at:at+2])==(0,0x7ff00000) else struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
        assert timer['active'] and timer['due']==clock['next'] and expiry==clock['expiry'],'Original instant healing clocks must preserve phase and exact expiry'
    return native

def compare_shields(block,domain,native):return compare_protections(block,domain,native)

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices)
    return compare_shields(block,domain,n)

def validate_rejection(block,name):raise AssertionError('Original shield definitions cannot be discarded')
