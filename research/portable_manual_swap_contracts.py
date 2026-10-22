"""Literal counts plus native call-order invariants for mode-swap reloads."""
EXPECTED={
    'ready-at-start':(1,1,5,995),'disabled':(0,0,6,94),'absent':(0,0,6,94),
    'no-condition':(0,0,6,94),'wrong-event':(0,0,6,94),'false-condition':(0,0,6,94),
    'other-owner':(0,0,6,94),'last-owner':(1,1,5,995),'gate-arrives':(1,1,4,997),
    'gate-expires-before-finish':(1,1,3,97),'speed':(1,1,8,992),'speed-expires-latched':(1,1,8,992),
    'fixed-zero':(2,1,11,989),'fixed-negative':(14,1,9,991),'charge-cancel':(1,1,4,996),
    'already-active':(0,0,11,989),'reenter':(3,2,4,100),'exhausted-budget':(3,2,3,99),
    'condition-alternative':(1,1,5,995),'cover-pump-order':(2,1,4,997),
    'charge-mode':(1,1,2,998),'non-weapon-effect':(0,0,6,94),'and-false':(0,0,6,94),'duplicate-trigger':(1,1,5,995),
}


def verify(case,native):
    label=case['name'].removeprefix('manual-swap-');expected=EXPECTED[label]
    flags=case.get('manual_swap',[False]*5);owner=flags.index(True) if any(flags) else 0
    observed=native['manual_swap'];queries=observed['queries'];ticks=observed['ticks'];conditions=observed['conditions']
    positive=[q for q in queries if q['result']];events=native['reload_events']
    starts=[e for e in events if e['kind']=='start'];finishes=[e for e in events if e['kind']=='finish']
    assert (len(positive),len(finishes),native['shots'][owner],native['ammo'][owner])==expected,(label,'counts',len(positive),len(finishes),native['shots'][owner],native['ammo'][owner])
    assert len(starts)==len(positive),(label,'no extra reload calls')
    for query,start in zip(positive,starts):
        assert (start['owner'],start['time'])==(query['owner'],query['time']),(label,'ready/start order')
        frame=next(f for f in ticks if f['owner']==query['owner'] and f['time']==query['time'])
        assert frame['hits']==0 and frame['after']['phase']=='ready',(label,'start consumes tick and cancels charge')
        assert frame['after']['reload_until']==start['until'],(label,'reload latch')
    for index,query in enumerate(queries):
        assert flags[query['owner']],(label,'disabled actor queried')
        relevant=[r for r in conditions if r['query']==index]
        assert query['result']==any(r['result'] for r in relevant),(label,'conditional weapon lookup')
        frame=next(f for f in ticks if f['owner']==query['owner'] and f['time']==query['time'])
        assert frame['before']['reload_until']<=0 and frame['before']['post_reload_until']<=0,(label,'busy reload queried')
    assert all(0<=r['query']<len(queries) for r in conditions),(label,'condition query identity')
    if label=='condition-alternative':assert [r['name'] for r in conditions]==['false-mode','swap-mode'],(label,'authored lookup order')
    if label in ('disabled','absent','already-active'):assert not queries,(label,'no ready call')
    if label in ('no-condition','wrong-event','other-owner','non-weapon-effect'):assert queries and not conditions,(label,'definition filter')
    if label in ('false-condition','and-false'):assert conditions and not any(r['result'] for r in conditions),(label,'false gate')
    if label=='charge-cancel':
        start=starts[0];frame=next(f for f in ticks if f['owner']==owner and f['time']==start['time'])
        assert frame['before']['phase']=='charging',(label,'existing charge must be interrupted')
    if label in ('ready-at-start','last-owner','speed','speed-expires-latched','condition-alternative','duplicate-trigger','charge-mode'):
        assert starts[0]['time']==0 and starts[0]['until']==(.3 if label.startswith('speed') else .6),(label,'duration latch')
        due=min(f['time'] for f in ticks if f['owner']==owner and f['time']>=starts[0]['until'])
        assert finishes[0]['time']==due,(label,'first actual frame at deadline')
    if label=='cover-pump-order':
        first=next(f for f in ticks if f['owner']==owner and f['time']==0)
        assert first['after']['sequence_index']==0,(label,'manual mode check precedes cover sequence')
    return dict(verified=True,reference_model_gap=False,ready_queries=len(queries),condition_queries=len(conditions),reload_starts=len(starts),reload_finishes=len(finishes),physical_shots=native['shots'][owner],authored_input_only=True)
