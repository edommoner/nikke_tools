"""Actual original-profile healing callbacks; no fabricated pool input."""
def verify(case,native):
    assert case['body']['squad'][0]=='델타 : 닌자 시프'
    events=native['healing_charge']['events'];builds=[e for e in events if e['kind']=='snapshot'];takes=[e for e in events if e['kind']=='take']
    assert native['projectile_shots']
    assert len(native['healing_charge']['definitions'])==case['contract']['definitions']
    if case['contract']['duration']==3 or not case['contract']['defender']:assert not builds and not takes
    else:assert len(builds)==7 and len(takes)==2 and all(e['value']>0 for e in takes),('original charge consumer',len(builds),len(takes))
    return dict(verified=True,original_definitions=True,declared_model=True,in_game_rules_verified=False,builds=len(builds),takes=len(takes),positive_takes=sum(e['value']>0 for e in takes),physical_shots=len(native['projectile_shots']))
