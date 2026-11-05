"""Literal owner, stage, notification order and reentry contracts."""


def verify(case,native):
    contract=case['contract'];events=native['ally_burst_events']
    casts=[i for i,e in enumerate(events) if e['kind']=='notify' and e['event']=='burst_cast']
    assert len(casts)==contract['casts'],(case['name'],'casts',casts)
    for i,start in enumerate(casts):
        chunk=events[start:casts[i+1] if i+1<len(casts) else len(events)]
        notices=[e for e in chunk if e['kind']=='notify'];assert len(notices)==7
        assert notices[1]['event'] in ('squad_burst_cast:1','squad_burst_cast:2','squad_burst_cast:3')
        assert notices[0]['owner']==notices[1]['owner']
        assert [(e['event'],e['owner']) for e in notices[2:]]==[('event:ally_burst_cast',j) for j in range(5)]
        current=None
        for event in chunk:
            if event['kind']=='notify':current=event
            else:
                assert current['owner']==event['owner']
                assert current['event'].startswith('squad_burst_cast:') or case['name'].endswith('before-ally-burst') and current['event']=='event:ally_burst_cast'
        assert len({e['time'] for e in chunk})==1
    actual=[e['owner'] for e in events if e['kind']=='activate'];assert actual==contract['listener_activations'],(case['name'],'activation order',actual,contract)
    hp=[a['hp'] for a in native['allies']];assert hp==contract['hp'],(case['name'],'hp',hp,contract['hp'])
    return dict(verified=True,reference_model_gap=False,casts=len(casts),listener_activations=len(actual),gpu_supported=False)
