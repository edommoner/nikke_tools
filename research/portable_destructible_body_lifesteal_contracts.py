"""Body-only lifesteal after the unchanged native landing; shield damage is not HP."""
def verify(case,native):
    label=case['contract']['label'];events=native['body_lifesteal'];attacks=native['typed']['attacks']
    assert native['typed']['finished'] and events
    assert all(r['caller']=='_land_boss' and r['after']>=r['before'] and r['rate']>=0 for r in events)
    positive=[r for r in events if r['rate']>0];heals=[r for r in positive if r['after']>r['before']]
    assert all(r['rate']==16.16 and r['heal']>=0 for r in positive)
    if label in ('hp','hit'):
        assert attacks
        # The scheduler owns these frame boundaries; keep exact times in the
        # oracle and use frame indices only to identify the authored shield span.
        assert not any(168<=round(r['time']*60)<192 for r in events)
        if case['contract']['duration']==3:assert not positive
        else:assert heals
    else:assert positive and heals
    if label=='stale-owner':assert not attacks
    if label=='break':assert len(attacks)==1 and attacks[0]['receipts'][0]['broken']
    return dict(verified=True,reference_model_gap=True,body_only_lifesteal=True,positive_body_heals=len(heals),shield_lifesteal=False,accumulation_verified=False,full_character_verified=False,in_game_rules_verified=False)
