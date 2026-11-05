"""Finite CPU truth versus the explicitly bounded shared live queue."""
BASE=35/60

def verify(case,native,trace):
    c=case['contract'];loops=c['loops'];names=[e['name'] for e in case['effects']]
    assert len(trace)==3+loops,(case['name'],len(trace))
    for i,p in enumerate(trace):
        assert names[p['row']]==('landing' if i<3 else 'loop-child')
        assert p['amount']==(3150 if i<3 else 1260) and p['recipients']==[0]
        assert abs(p['created']-BASE)<1e-12 and abs(p['landed']-BASE)<1e-12
    assert native['damage']==[10418+1260*loops,1,1,1,1]
    want=[dict(owner=0,name='late-child',hits=1)] if c['late'] else []
    assert native['full_burst_capacity']['entries']==want
    legacy=int(c['legacy']);assert native['pending_burst']==dict(count=legacy,enqueued=legacy,fired=0)
    calls=native['full_burst_queue']['calls'];resolved=[r for r in calls if r['resolved']]
    assert len(resolved)==1+loops and resolved[0]['name']=='landing'
    assert all(r['name']=='loop-child' and r['full'] for r in resolved[1:])
    assert all(abs(r['time']-BASE)<1e-12 and r['full'] for r in resolved)
    late=[r for r in calls if r['name']=='late-child']
    assert len(late)==int(c['late']) and all(not r['resolved'] and r['full'] for r in late)
    return dict(verified=True,native_finite=True,queued_for_generation=1+loops,packet_count=len(trace),final_deferred=want,shared_capacity_rejection=c['reject'])
