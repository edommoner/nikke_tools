"""Literal query order, ignored live count and HP attack results from native handlers."""
BASE=35/60
def verify(case,native,trace):
    kind,mode=case['contract']['kind'],case['contract']['mode'];zero=kind in ('zero','zero-parts','negative');reference=kind in ('reference','ignored-live-1024');hits=0 if zero else 1 if reference else 3
    amount=3780 if mode=='max_hp_additive' else 472
    assert native['damage']==[968+(amount+(11340 if mode=='max_hp_additive' else 1418) if kind=='parts' else amount)*hits,1,1,1,1],(case['name'],native['damage'])
    assert len(trace)==hits and all(p['amount']==amount and p['recipients']==[0] and abs(p['created']-BASE)<1e-12 and abs(p['landed']-BASE)<1e-12 for p in trace)
    expected=[dict(kind=1,time=BASE,flat=0,percent=110)]
    if reference:expected.append(dict(kind=2,time=BASE,present=True,value=1024 if kind=='ignored-live-1024' else 2))
    if mode is not None:expected.append(dict(kind=3,time=BASE,maximum=2000))
    actual=native['full_burst_query'];assert len(actual)==len(expected),(case['name'],actual)
    for a,b in zip(actual,expected):
        assert a.keys()==b.keys() and abs(a['time']-b['time'])<1e-12 and all(a[k]==b[k] for k in b if k!='time'),(case['name'],actual)
    calls=native['full_burst_landing']['calls'];assert len(calls)==2 and not calls[0]['resolved'] and calls[1]['resolved']
    assert calls[1]['latched']==(-2 if kind=='negative' else 0 if kind in ('zero','zero-parts') else hits)
    return dict(verified=True,packets=hits,ordered_queries=len(expected),ignored_live_overflow=kind=='ignored-live-1024',zero_hit_no_arithmetic=zero)
