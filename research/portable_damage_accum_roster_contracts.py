"""Fixed original-profile activation coverage, not full character certification."""
def verify(case,native):
    profile=case['contract']['profile'];duration=case['contract']['duration'];data=native['damage_accumulation'];events=data['events']
    expected={('도로시',3):(73,0,0,[]),('도로시',30):(73,2,2,[10593140]),('트로니',3):(74,1,0,[]),('트로니',30):(74,7,4,[2184012,7372327,7162860,7601330])}[(profile,duration)]
    definitions,builds,full,emissions=expected
    assert len(data['definitions'])==definitions
    assert sum(e['kind']=='snapshot' for e in events)==builds
    assert sum(e['kind']=='full-notice' for e in events)==full
    assert [e['amount'] for e in events if e['kind']=='emission']==emissions
    takes=[e['value'] for e in events if e['kind']=='take'];assert len(takes)==len(emissions) and all(v>0 for v in takes)
    assert native['projectile_shots']
    return dict(verified=True,definitions=definitions,builds=builds,full_notices=full,positive_takes=len(takes),emissions=emissions,declared_model=True,in_game_rules_verified=False)
