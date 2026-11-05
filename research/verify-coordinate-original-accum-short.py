"""Original accumulation uses shared collection, packet and final-state proofs."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('original_accum_parent',ROOT/'research/verify-coordinate-original-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_original_cases import prepare_case
from portable_coordinate_original_accum_cases import fixtures
from world_damage_accum_native import capture
from portable_damage_accum_observation import compare_final
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_shared_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);c['accum_witness']=row['accum_witness'];c['coordinate_packet_history']='ordered-sha256-v1'
        w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def verify_witness(case,native):
    events=native['damage_accumulation']['events'];takes=[e for e in events if e['kind']=='take'];emissions=[e for e in events if e['kind']=='emission']
    if case['accum_witness']=='control':assert not takes and not emissions
    else:
        assert takes and emissions,'Original release must actually execute'
        assert any(e['value']>0 for e in takes) and all(e['amount']>0 for e in emissions)
        for take in takes:
            effect=case['effects'][take['row']]
            assert effect['stat']=='accum_split_damage' and effect['target_effect']==take['name']
            assert take['requester']==case['owners'][take['row']]
            assert all(p['current']==0. and p['done'] for p in take['after']['pools'] if p['name']==take['name']),'Discharge must consume and mark the live pool'
            assert take['after']['archive'][take['name']]==0.
        if case['names'][0]=='도로시':
            assert all('event:state_end:낙인' in case['effects'][e['row']]['trigger']['timing'] for e in takes)
            assert len(takes)==len(emissions)==1
            snapshots=[e for e in events if e['kind']=='snapshot'];notices=[e for e in events if e['kind']=='full-notice']
            assert len(snapshots)==len(notices)==1 and notices[0]['time']<takes[0]['time']
            duration=case['effects'][snapshots[0]['row']]['duration']
            assert 0<=takes[0]['time']-(snapshots[0]['time']+duration)<1/60
            assert all(not any(p['name']==e['name'] for p in e['before']['pools']) for e in takes),'Expiry must retire the carrier before release'
            assert takes[0]['value']==snapshots[0]['after']['pools'][0]['base']
        else:
            notices=[e for e in events if e['kind']=='full-notice' and e['name']=='누적 폭발 스킬']
            assert len(notices)==len(takes)==len(emissions)==4
            assert [e['time'] for e in notices]==[e['time'] for e in takes]==[e['time'] for e in emissions]
            for take in takes:
                pool=next(p for p in take['before']['pools'] if p['name']==take['name'])
                assert pool['current']==pool['base']==take['value'] and pool['done']
            assert all('event:accum_full:누적 폭발 스킬' in case['effects'][e['row']]['trigger']['timing'] for e in takes)
    return True

def native_reference(domain):
    with capture(domain[0]['names'],identity_rows=True) as observed:n=parent.native_reference(domain)
    n['damage_accumulation']=observed;verify_witness(domain[0],n);return n

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    from portable_runtime import decode
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices);compare_final(block,domain[1],n['damage_accumulation'])
    actual=decode(block[:159744],domain[1]);takes=n['damage_accumulation']['events']
    for index,source in enumerate(domain[1]['binding_source_indices']):
        if domain[0]['effects'][source].get('stat')=='accum_split_damage':assert actual['timers'][index]['activations']==sum(e['kind']=='take' and e['row']==source for e in takes),'Every original release dispatch must execute'
    return n

def validate_rejection(block,name):raise AssertionError('Original accumulation definitions cannot be discarded')
