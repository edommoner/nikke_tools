"""Literal counts, damage, ammo and observer source identity contracts."""
def verify(case,native):
    expected=case['contract'];obs=native['ammo_equivalent'];owner=expected['owner'];notices=obs['notices'];calls=obs['calls']
    assert len(notices)==expected['notices']==obs['squad_count'],(case['name'],'squad count',len(notices),obs['squad_count'])
    assert all(n['owner']==owner and n['origin'] in ('physical','equivalent') for n in notices),(case['name'],'notice source',notices)
    assert len(calls)==expected['calls'] and [c['name'] for c in calls]==expected['call_names'],(case['name'],'dispatch count',calls)
    assert [c['value'] for c in calls]==expected['call_values'] and all(c['owner']==owner for c in calls),(case['name'],'literal caster quantity',calls)
    assert [c['from_tick'] for c in calls]==expected.get('tick_calls',[False]*len(calls)),(case['name'],'tick phase',calls)
    assert obs['stacks']==([dict(owner=expected['watcher'],stack=expected['stack'])] if expected['stack'] else []),(case['name'],'watcher',obs['stacks'])
    shots=native['projectile_shots']
    assert all(s['owner']==owner for s in shots),(case['name'],'shot owner',shots)
    assert [s['damage'] for s in shots]==expected['packet_damage'],(case['name'],'damage',shots)
    assert [s['pellets']*s['muzzles'] for s in shots]==expected['packet_counts'],(case['name'],'split',shots)
    damage=sum(a*b for a,b in zip(expected['packet_damage'],expected['packet_counts']))
    assert native['damage']==[damage if i==owner else 0 for i in range(5)],(case['name'],'totals',native['damage'])
    assert native['ammo'][owner]==expected['ammo'],(case['name'],'physical ammo',native['ammo'])
    times=[s['time'] for s in shots]
    assert all(n['time'] in times for n in notices),(case['name'],'notice times',notices)
    assert [sum(n['time']==time for n in notices) for time in times]==expected['notice_groups'],(case['name'],'per-frame notifications',notices)
    for i,time in enumerate(times):
        origins=[n['origin'] for n in notices if n['time']==time];count=expected['notice_groups'][i]
        literal=['equivalent']*count if case['name'].endswith('infinite-ammo') else ['equivalent']*(count-1)+['physical'] if expected['extras_before_physical'][i] else ['physical']+['equivalent']*(count-1)
        assert origins==literal,(case['name'],'origin order',origins)
    assert all(c['time']==0 if case['name'].endswith('battle-start') else c['time'] in times or c['from_tick'] for c in calls),(case['name'],'dispatch times',calls)
    assert len([n for n in notices if n['origin']=='physical'])==(0 if case['name'].endswith('infinite-ammo') else len(shots)),(case['name'],'physical notices',notices)
    return dict(verified=True,reference_model_gap=False,notices=len(notices),instant_dispatches=len(calls),physical_shots=len(shots),ammo_decrement_notification_independent=True)
