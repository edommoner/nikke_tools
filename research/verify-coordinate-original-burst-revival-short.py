"""Full original B1 revival through the shared coordinate battle and revival trace."""
import array,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('burst_revival_original_parent',ROOT/'research/verify-coordinate-original-short.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
from portable_coordinate_original_burst_revival_cases import fixtures
from portable_coordinate_original_cases import prepare_case
from world_revive_native import capture
from world_revival_compare import compare_revival_state
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_clock_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    baseline={e['name']:e for e in json.loads((ROOT/'tests/fixtures/portable-original-burst-revival-clock-retention.json').read_text())['entries']}
    for row in fixtures():
        c,p=prepare_case(row);c.update(observe_skill_clocks=True,observe_revival_attempts=True,expected_down_owners=row['expected_down_owners'],expected_revived_owners=row['expected_revived_owners']);w,m,b,d=compile_coordinate_battle(p);single=array.array('I',w)
        if sys.byteorder!='little':single.byteswap()
        assert hashlib.sha256(single.tobytes()).hexdigest()==baseline[c['name']]['input_sha256'],'Original pre-clock input must be byte-identical'
        rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,words,_ in rows:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    with capture(domain[0]) as events:n=parent.native_reference(domain)
    n['original_revival_events']=events
    n['original_skill_clocks']=n['battle'].pop('skill_clocks')
    verify_witness(domain[0],n)
    baseline=json.loads((ROOT/'tests/fixtures/portable-original-burst-revival-clock-retention.json').read_text())['entries']
    expected=next(e for e in baseline if e['name']==domain[0]['name'])
    projected=dict(n);projected.pop('original_skill_clocks')
    projected['original_revival_events']=[e for e in projected['original_revival_events'] if e['kind']!='skill-clock-reduction']
    assert cross.digest(projected)==expected['native_sha256'],'Original pre-clock native values must be retained'
    return n

def verify_witness(case,n):
    events=n['original_revival_events'];downs=[e for e in events if e['kind']=='after-down'];ups=[e for e in events if e['kind']=='after-revive'];actions=[e for e in events if e['kind']=='action-revive'];attempts=[e for e in events if e['kind']=='revive-attempt']
    assert [e['owner'] for e in downs]==case['expected_down_owners']
    assert [e['owner'] for e in ups]==[e['owner'] for e in actions]==case['expected_revived_owners']
    assert len(attempts)==(0 if case['name'].endswith('only-B3-down') else 1),'Count actual six-second B1 dispatches, including zero-target casts'
    for event,action in zip(ups,actions,strict=True):
        who=event['owner'];maximum=n['battle']['allies'][who]['max_hp'];hp=maximum*81.67/100
        assert event['state']['hp'][who]==hp and event['state']['hp_pct'][who]==hp/maximum*100
        assert event['time']>downs[0]['time'] and event['time']==attempts[0]['time']==action['time']
        assert action['ammo']>0 and action['next_fire']==action['time'] and action['charge_phase']=='ready' and not action['charging']
        assert any(e['kind']=='target' and e['owner']==0 and e['result']==[who] for e in events)
    for who in case['expected_down_owners']:assert n['battle']['allies'][who]['down']==(who not in case['expected_revived_owners'])
    if len(case['expected_down_owners'])==2:
        reductions=[e for e in events if e['kind']=='skill-clock-reduction'];assert reductions,'Original Centi must really invoke remaining-clock reduction'
        assert any(any(after['row']==before['row'] and after['due']<before['due'] for before in e['before'] for after in e['after']) for e in reductions),'At least one actual next-fire deadline must move earlier'
        before=next(e for e in events if e['kind']=='before-revive')['state']['down'];assert 3 in before and 4 in before,'Both real candidates must exist at selection time'
    return True

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices)
    clock_spec=importlib.util.spec_from_file_location('original_shared_clock_comparator',ROOT/'research/verify-world-skill-interval-short.py');clocks=importlib.util.module_from_spec(clock_spec);clock_spec.loader.exec_module(clocks)
    actual_clocks=clocks.clock_state(block,domain[1])
    for row in actual_clocks:row['row']=domain[1]['binding_source_indices'][row['row']]
    assert actual_clocks==n['original_skill_clocks'],'Existing common remaining skill-clock reduction must match native'
    compare_revival_state(block,domain[0],dict(revival_events=n['original_revival_events']))
    from portable_runtime import decode
    actual=decode(block[:159744],domain[1]);attempts=[e for e in n['original_revival_events'] if e['kind']=='revive-attempt']
    for index,source in enumerate(domain[1]['binding_source_indices']):
        if domain[0]['effects'][source].get('stat')=='revive':assert actual['timers'][index]['activations']==sum(e['row']==source for e in attempts),'GPU must execute each original attempt, including zero-target cast'
    for index,source in enumerate(domain[1]['binding_source_indices']):
        if domain[0]['effects'][source].get('stat')=='skill_cooldown_reduce_pct':assert actual['timers'][index]['activations']==sum(e['kind']=='skill-clock-reduction' and e['row']==source for e in n['original_revival_events']),'Each native remaining-clock reduction must execute on GPU'
    return n

def validate_rejection(block,name):raise AssertionError('Original burst-revival definitions cannot be discarded')
