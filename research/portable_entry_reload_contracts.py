"""Independent invariants of actual full-world entry/query/shot ordering."""


def verify(case,native):
    name=case['name'].removeprefix('entry-reload-');events=native['entry_reload'];frames=events['frames'];queries=events['queries']
    owner=case['owners'][-1];mode=case['effects'][-1]
    assert frames and all(f['owner']==owner for f in frames),(name,'mode owner')
    measured=next((d['value'] for d in case.get('entry_delays',[]) if d['name']==mode['name'] and d['owner']==owner),None)
    enabled=bool(mode.get('entry_reload')) and measured is None
    assert len(queries)==(len(frames) if enabled else 0),(name,'one actual duration query per mode tick, including after entry')
    first_values={'speed--50':.6*1.5,'speed-50':.3,'speed-100':0.,'speed-150':0.,'speed-sum':.15,'fixed-0':0.,'fixed-0.2':.2,'fixed--0.2':-.2,'fixed-max':.4,'fixed-ignores-speed':.2,'speed-expires-latched':.3,'fixed-expires-latched':.4,'named-child-before-first-query':.3}
    expected=first_values.get(name,.6)
    if enabled:
        assert queries[0]['result']==expected,(name,'initial duration',queries[0]['result'],expected)
        for i,q in enumerate(queries):
            assert q['frame']==i and q['owner']==owner and q['time']==frames[i]['time'],(name,'query ordering')
            assert q['base_reload']==.6,(name,'query must use restored BASE weapon, not mode .9')
        final_values={'speed-expires-latched':.6,'speed-arrives-latched':0.,'fixed-expires-latched':.6,'fixed-arrives-latched':.2}
        assert queries[-1]['result']==final_values.get(name,expected),(name,'current modifiers still queried after latching')
    sessions=[]
    for i,f in enumerate(frames):
        before=f['before'];after=f['after'];wait=before['entry_until']
        if before['new_session'] and wait<0:
            sessions.append(f)
            if enabled or measured is not None:wait=f['time']+(queries[i]['result'] if enabled else measured)
        if wait>=0 and f['time']<wait:
            assert after['entry_until']==wait and after['new_session'] and f['hits']==0,(name,'latched wait must survive modifier changes')
        elif enabled or measured is not None:
            assert not after['new_session'],(name,'entry completed before physical action')
    assert len(sessions)==(3 if name=='reenter' else 1),(name,'physical mode sessions')
    assert len(events['entries'])==len(sessions),(name,'logical entry and physical session correspondence')
    assert all(e['after']['reload_until']==-1 and e['after']['phase']=='ready' for e in events['entries']),(name,'existing native session reset before waiting')
    if name in ('finite-before-wait-end','reenter'):assert not any(f['hits'] for f in frames),(name,'expired waiting session must not shoot')
    else:
        initial=frames[0]['time'];delay=expected if enabled else measured or 0.
        complete=next(f for f in frames if f['time']>=initial+delay)
        if mode['charge']:
            assert complete['after']['charge_start']==complete['time'],(name,'charge starts after entry')
            threshold=complete['time']+.2
        else:threshold=complete['time']
        first=next((f for f in frames if f['hits']),None)
        assert first is not None,(name,'finite wait must eventually allow a shot')
        if first is not None:
            assert first['time']>=threshold,(name,'no pre-entry/pre-charge shot')
            if name!='during-base-reload':assert first['time']==next(f['time'] for f in frames if f['time']>=threshold),(name,'no invented post-entry delay')
    if name=='cover-delays-entry':assert frames[0]['time']>=.2,(name,'control gate precedes entry')
    if name=='during-base-charge':assert events['entries'][0]['before']['phase']=='charging',(name,'fixture must interrupt existing charge')
    if name=='during-base-reload':assert events['entries'][0]['before']['reload_until']>events['entries'][0]['time'],(name,'fixture must enter during actual reload')
    if name=='fixed--0.2':assert frames[0]['after']['entry_until']==-.2 and frames[0]['hits']>0,(name,'negative fixed time is not clamped')
    return dict(verified=True,frames=len(frames),duration_queries=len(queries),sessions=len(sessions))
