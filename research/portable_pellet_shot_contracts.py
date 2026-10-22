"""Literal notification identity, order, snapshot and damage contracts."""
def verify(case,native):
    expected=case['contract'];observed=native['pellet_shot'];notices=observed['notices'];owner=expected['owner']
    assert [n['raw'] for n in notices]==expected['notices'],(case['name'],'raw identities/order',notices)
    assert [n['count'] for n in notices]==expected['counts'],(case['name'],'captured count',notices)
    assert all(n['owner']==owner for n in notices),(case['name'],'owner',notices)
    stacks={name:observed['stacks'].get(name,0) for name in expected['stacks']}
    assert stacks==expected['stacks'] and not set(observed['stacks'])-set(stacks),(case['name'],'stacks',observed['stacks'])
    shots=[shot for shot in native['projectile_shots'] if shot['owner']==owner]
    assert [s['damage'] for s in shots]==expected['packet_damage'],(case['name'],'packet damage',shots)
    assert [s['pellets']*s['muzzles'] for s in shots]==expected['packet_counts'],(case['name'],'packet count',shots)
    total=sum(d*n for d,n in zip(expected['packet_damage'],expected['packet_counts']))
    assert native['damage']==[total if i==owner else 0 for i in range(5)],(case['name'],'total',native['damage'])
    assert all(n['time'] in [s['time'] for s in shots] for n in notices),(case['name'],'notification time',notices)
    events=observed['events']
    assert all(e['time'] in [s['time'] for s in shots] for e in events),(case['name'],'event outside shot',events)
    for shot in shots:
        selected=[e['event'] for e in events if e['time']==shot['time']]
        expected_notices=['pellet_hit_in_shot:'+n['raw'] for n in notices if n['time']==shot['time']]
        # Auto fire completes every pellet before per-shot notices, then attack
        # and muzzle hit_count. Charge emits neither per-shot notice nor pellet
        # notice for a single packet, but our charge control is five pellets.
        assert selected==['pellet_hit']*(shot['pellets']*shot['muzzles'])+expected_notices+['on_attack']+['hit_count']*shot['muzzles'],(case['name'],'notify order',selected)
    return dict(verified=True,reference_model_gap=False,shots=len(shots),notices=len(notices),raw_identity_preserved=True)
