"""Original owned-source/ammo execution, shared observers and full battle proof."""
import array,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('original_owned_parent',ROOT/'research/verify-coordinate-original-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_original_cases import prepare_case
from portable_coordinate_original_owned_cases import fixtures
from world_original_periodic_source_native import capture as capture_sources
from world_ammo_equivalent_native import capture as capture_ammo
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_shared_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);c['owned_witness']=row['owned_witness'];c['coordinate_packet_history']='ordered-sha256-v1'
        w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def verify_witness(case,n):
    sources=n['original_owned_sources'];ammo=n['ammo_equivalent']
    assert len(ammo['notices'])==ammo['squad_count']
    if case['owned_witness']=='Ein':
        from periodic_source_specs import LEGACY_WARNING
        assert LEGACY_WARNING in sources['model_warnings']
        events=sources['dispatches'];assert events and events[0]['time']==0 and len(events[0]['after'][0]['expiry'])==4
        assert len(sources['final'])==1 and sources['final'][0]['legacy'] and sources['final'][0]['epoch']==len(events)
        for event in events:
            effect=case['effects'][event['row']];record=event['after'][0]
            assert record['expiry']==[None if life<0 else event['time']+life for life in effect['feather_slots']]
            assert record['refreshed']==event['time'] and record['row']==event['row']
        assert {k:v for k,v in sources['final'][0].items() if k!='next_at'}=={k:v for k,v in events[-1]['after'][0].items() if k!='next_at'}
        if case['duration']>1:
            assert len(events)==2 and events[1]['time']>0 and len(events[1]['after'][0]['expiry'])==6 and events[1]['after'][0]['epoch']==2
            assert sources['ticks'] and any(r['row']==2 for r in n['skill_trace'])
            assert {r['created'] for r in n['skill_trace'] if r['row']==2}=={r['time'] for r in sources['ticks']}
            assert len({r['time'] for r in sources['ticks']})==len(sources['ticks'])
            for tick in sources['ticks']:
                source=tick['sources'][0];assert 0<=tick['time']-source['next_at']<1/60
                live=sum(t is None or t>tick['time'] for t in source['expiry'])
                assert sum(r['row']==2 and r['created']==tick['time'] for r in n['skill_trace'])==live,'Every live feather must create its real damage packet'
        else:assert len(events)==1 and not sources['ticks']
        if case['duration']==40:assert sum(t is None or t>case['duration'] for t in sources['final'][0]['expiry'])==2
        assert not ammo['calls']
    else:
        assert not sources['dispatches'] and not sources['final']
        calls=ammo['calls'];extra=[r for r in ammo['notices'] if r['origin']!='physical']
        if case['duration']==3:assert not calls and not extra
        else:
            assert calls and all(r['value']==40. and r['owner']==0 and not r['from_tick'] for r in calls)
            assert len(extra)==39*len(calls)
            for call in calls:assert sum(r['time']==call['time'] and r['owner']==call['owner'] and r['origin']==call['name'] for r in extra)==39
    return True

def native_reference(domain):
    with capture_ammo(domain[0]) as ammo,capture_sources(domain[0]) as sources:n=parent.native_reference(domain)
    n.update(original_owned_sources=sources,ammo_equivalent=ammo);verify_witness(domain[0],n);return n

def compare(block,domain):
    from portable_runtime import decode
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices)
    return compare_owned_state(decode(block[:159744],domain[1]),domain,n)

def compare_owned_state(actual,domain,n):
    c,m,_,_=domain
    for index,row in enumerate(m['binding_source_indices']):
        effect=c['effects'][row];stat=effect.get('stat')
        for slot,timing in enumerate(effect.get('trigger',{}).get('timing',[])):
            if timing.startswith('squad_ammo_consume:'):assert actual['timers'][index]['trigger_counts'][slot]==n['ammo_equivalent']['squad_count'],'Every physical and equivalent ammo notice must reach the original counted trigger'
        if stat=='feather_refresh':assert actual['timers'][index]['activations']==sum(r['row']==row for r in n['original_owned_sources']['dispatches'])
        if stat=='squad_ammo_consume_as':assert actual['timers'][index]['activations']==len(n['ammo_equivalent']['calls'])
    expected=[]
    for r in n['original_owned_sources']['final']:
        expected.append(dict(owner=r['owner'],name=r['name'],definition=m['binding_source_indices'].index(r['row']),epoch=r['epoch'],legacy=r['legacy'],scheduled=r['next_at'] is not None,count=sum(t is None or t>c['duration'] for t in r['expiry']),refreshed=r['refreshed'],next_at=r['next_at']))
    def bits(v):
        if isinstance(v,float):return struct.pack('<d',v).hex()
        if isinstance(v,dict):return {k:bits(x) for k,x in v.items()}
        if isinstance(v,list):return [bits(x) for x in v]
        return v
    assert bits(actual['periodic_sources'])==bits(expected),'Actual owned population, epoch and clock must match'
    return n

def validate_rejection(block,name):raise AssertionError('Original owned effects cannot be discarded')
