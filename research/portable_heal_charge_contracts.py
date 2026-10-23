"""Literal pool amounts and lifecycle order for the declared received-heal model."""
TAKES={
 'empty':[0], 'full-HP':[1000], 'damaged':[1000], 'capacity-clamp':[1500],
 'zero-capacity':[0], 'negative-capacity':[0], 'negative-heal':[0],
 'live-bonus':[3000], 'wrong-bonus-name':[1500], 'unrestricted-bonus':[3000],
 'expired-bonus-keeps-amount':[3000], 'source-ATK-snapshot':[1500], 'initial-ATK':[3000],
 'one-discharge':[1500,0], 'missing-name':[0], 'refresh-resets-quantity':[0],
 'named-removal-retains':[1000], 'cleanse-discards':[0], 'ordered-duplicate-recipients':[1000],
 'live-other-pool-receives-release':[1000], 'source-outgoing-and-received':[2250],
 'lifesteal':[900], 'down-discards':[], 'repair-does-not-deposit':[0],
 'shared-scalar-pool':[1500], 'other-owner':[1000], 'other-caster-bonus':[2250],
 'owner-order-before-activation':[0], 'other-caster-bonus-late-in-order':[1500],
}
def verify(case,native):
    kind=case['contract']['kind'];events=native['healing_charge']['events'];takes=[e for e in events if e['kind']=='take'];expected=TAKES[kind]
    assert [e['value'] for e in takes]==expected,(kind,[e['value'] for e in takes],expected)
    assert all(e['owner']==(4 if kind in ('other-owner','owner-order-before-activation') else 0) for e in takes)
    releases=[e for e in events if e['kind']=='discharge'];assert [e['taken'] for e in releases]==expected
    assert all(e['targets']==([1,2,1] if kind=='ordered-duplicate-recipients' else list(range(5))) for e in releases)
    for index,e in enumerate(events):
        if e['kind']!='discharge':continue
        children=events[index+1:e['returned_sequence']]
        taken=next(i for i,c in enumerate(children) if c['kind']=='take')
        heals=[(i,c) for i,c in enumerate(children) if c['kind']=='collect']
        assert [c['owner'] for i,c in heals]==e['targets'] and all(i>taken for i,c in heals)
        factor=2.25 if kind=='source-outgoing-and-received' else 1
        assert all(c['amount']==e['taken']*factor for i,c in heals)
    for e in takes:
        if e['name']=='pool':
            ids={i for i,eff in enumerate(case['effects']) if eff.get('stat')=='heal_overcharge_store_atk_pct' and eff.get('name')=='pool'}
            matched=[p for p in e['after'] if p['owner']==e['owner'] and p['row'] in ids]
            if e['value']>0:assert matched
            assert all(p['done'] and p['current']==0 and not p['ended'] for p in matched)
    if kind=='expired-bonus-keeps-amount':
        # Ended pool retains quantity above its now-lower capacity until release.
        assert any(not p['active'] and p['ended'] and p['current']==3000 for e in events for p in e['after'])
    if kind=='source-ATK-snapshot':assert {p['base'] for e in events for p in e['after']}=={1500}
    if kind=='refresh-resets-quantity':
        snapshots=[e for e in events if e['kind']=='snapshot'];assert len(snapshots)==2
        assert any(p['current']==1500 for p in snapshots[-1]['before']) and all(p['current']==0 for p in snapshots[-1]['after'])
    if kind=='damaged':assert [a['hp'] for a in native['allies']]==[7000,6000,6000,6000,6000]
    if kind=='ordered-duplicate-recipients':assert [a['hp'] for a in native['allies']]==[6000,7000,6000,5000,5000]
    if kind=='negative-heal':assert native['allies'][0]['hp']==9000
    if kind=='down-discards':assert native['allies'][0]['down'] and native['allies'][0]['hp']==0
    return dict(verified=True,reference_model_gap=False,declared_model=True,in_game_rules_verified=False,pool_takes=expected,discharges=len(releases),observer_events=len(events))
