"""Literal live-queue order and numeric/timing ownership, not GPU-derived expectations."""
BASE=35/60

def verify(case,native):
    kind=case['contract']['kind'];o=native['full_burst_queue'];packets=o['packets'];names=[e['name'] for e in case['effects']]
    rows=[dict(name=names[r['row']],created=r['created'],landed=r['landed'],amount=r['amount'],recipients=r['recipients']) for r in packets]
    prefix=[('landing',3150,[0],BASE,BASE)]*3
    if kind=='live-once':expected=prefix+[('deferred-child',1260,[0],BASE,BASE)]
    elif kind=='live-nested':expected=prefix+[('deferred-child',1260,[0],BASE,BASE),('deferred-grandchild',1260,[0],BASE,BASE)]
    elif kind=='live-initial-and-nested':expected=prefix+[('deferred-child',1260,[0],BASE,BASE)]*2
    elif kind=='legacy-tail-next-collection':expected=prefix
    elif kind.startswith('periodic'):
        expected=prefix+[('ordinary-prefix',630,[0],BASE,.6)]+[('parts-source',1260,[0,1,2],t,t) for t in (.6,41/60,47/60)]
    else:expected=prefix+[('ordinary-prefix',630,[0],BASE,.6),('parts-source',1260,[0],BASE,.6)]
    assert len(rows)==len(expected),(case['name'],rows)
    for actual,(name,amount,targets,created,landed) in zip(rows,expected):
        assert actual['name']==name and actual['amount']==amount and actual['recipients']==targets,(case['name'],actual)
        assert abs(actual['created']-created)<1e-12 and abs(actual['landed']-landed)<1e-12
    want=dict(count=1,enqueued=1,fired=0) if kind=='legacy-tail-next-collection' else dict(count=0,enqueued=0,fired=0)
    assert native['pending_burst']==want,(case['name'],native['pending_burst'])
    resolved=[r['name'] for r in o['calls'] if r['resolved']]
    expect=['landing']+(['deferred-child','deferred-grandchild'] if kind=='live-nested' else ['deferred-child']*2 if kind=='live-initial-and-nested' else ['deferred-child'] if kind=='live-once' else [])
    assert resolved==expect and all(r['full'] and abs(r['time']-BASE)<1e-12 for r in o['calls'] if r['resolved'])
    if kind in ('parts-receipt-tail','interrupt-receipt-tail'):
        p=[r for r in native['parts_skill_events'] if r['kind']=='packet'];extra=kind.startswith('interrupt')
        assert [r['damage'] for r in p]==[1260,1890,1890]+([1260] if extra else [])
        assert p[0]['part_damage']==1890 and p[0]['reach']==5 and p[0]['interrupt_reach']==int(extra) and p[0]['interrupt_damage']==(1260 if extra else 0)
        if extra:assert native['parts_skill_accounting']==dict(interrupt_damage=[1260,0,0,0,0],extra=[dict(identity=0,generation=1,extra_hits=1,extra_dealt=1260)])
    return dict(verified=True,reference_model_gap=False,packets=len(rows),resolved_handlers=resolved,legacy_pending=want,kind=kind)
