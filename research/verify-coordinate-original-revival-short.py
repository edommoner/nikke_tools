"""Original down/revival callbacks composed with shared sampled coordinate execution."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('revival_original_parent',ROOT/'research/verify-coordinate-original-short.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
from portable_coordinate_original_revival_cases import fixtures
from portable_coordinate_original_cases import prepare_case
from world_revive_native import capture
from world_revival_compare import compare_revival_state
suite=parent.suite;cross=parent.cross;SOURCE=parent.SOURCE;INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);c['expected_downs']=row['expected_downs'];w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,words,_ in rows:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    with capture(domain[0]) as events:n=parent.native_reference(domain)
    n['original_revival_events']=events
    verify_witness(domain[0],n)
    return n

def verify_witness(case,n):
    events=n['original_revival_events'];count=case['expected_downs']
    downs=[e for e in events if e['kind']=='after-down'];ups=[e for e in events if e['kind']=='after-revive'];actions=[e for e in events if e['kind']=='action-revive']
    assert len(downs)==count and all(e['owner']==3 for e in downs)
    assert len(ups)==len(actions)==min(count,1),'Original Gamma state must allow exactly the first revival'
    if count:
        assert ups[0]['owner']==3 and ups[0]['time']==downs[0]['time']==actions[0]['time']
        maximum=n['battle']['allies'][3]['max_hp'];hp=maximum*96/100
        assert ups[0]['state']['hp'][3]==hp and ups[0]['state']['hp_pct'][3]==hp/maximum*100
        assert 3 not in ups[0]['state']['down']
        assert actions[0]['ammo']>0 and actions[0]['next_fire']==actions[0]['time']
        assert actions[0]['charge_phase']=='ready' and not actions[0]['charging']
        removed=[e for e in n['original_named_removals'] if e['target']=='매터 감마']
        assert len(removed)==count and removed[0]['before']>0 and removed[0]['after']==0
    assert n['battle']['allies'][3]['down']==(count==2)
    if count==2:assert n['battle']['allies'][3]['hp']==0 and downs[1]['time']>ups[0]['time']
    return True

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices)
    compare_revival_state(block,domain[0],dict(revival_events=n['original_revival_events']))
    from portable_runtime import decode
    actual=decode(block[:159744],domain[1]);revives=[i for i,source in enumerate(domain[1]['binding_source_indices']) if domain[0]['effects'][source].get('stat')=='revive']
    assert len(revives)==1
    assert actual['timers'][revives[0]]['activations']==min(domain[0]['expected_downs'],1),'Only the original first ally-down may revive'
    return n

def validate_rejection(block,name):raise AssertionError('Original revival definitions cannot be discarded')
