"""Literal broadcast, caster/owner, recipient, budget and reentry contracts."""
def verify(case,native):
    contract=case['contract'];events=native['ally_burst_events']
    casts=[i for i,e in enumerate(events) if e['kind']=='notify' and e['event']=='burst_cast']
    assert len(casts)==contract['casts'],(case['name'],'casts',casts)
    for n,start in enumerate(casts):
        chunk=events[start:casts[n+1] if n+1<len(casts) else len(events)]
        notices=[e for e in chunk if e['kind']=='notify']
        assert len(notices)==7,(case['name'],'notification count',notices)
        assert notices[1]['event'].startswith('squad_burst_cast:'),(case['name'],'stage notice')
        assert [(e['event'],e['owner']) for e in notices[2:]]==[('event:ally_burst_cast',i) for i in range(5)],(case['name'],'squad order')
        assert len({e['time'] for e in chunk})==1,(case['name'],'synchronous notifications')
        current=None
        for event in chunk:
            if event['kind']=='notify':current=event
            else:assert current['event']=='event:ally_burst_cast' and current['owner']==event['owner'],(case['name'],'activation notification context')
    assert [e['owner'] for e in events if e['kind']=='activate']==contract['listener_activations'],(case['name'],'activation order',events)
    assert [a['hp'] for a in native['allies']]==contract['hp'],(case['name'],'health',[a['hp'] for a in native['allies']])
    return dict(verified=True,reference_model_gap=False,casts=len(casts),broadcasts=len(casts)*5,listener_activations=len(contract['listener_activations']))
