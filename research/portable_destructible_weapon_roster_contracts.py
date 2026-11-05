"""Real definition completeness and positive late modifier exercise."""
def verify(case,native):
    c=case['contract'];rows=native['typed']['attacks'];samples=native['shield_samples']
    assert len(rows)==(22 if c['duration']==30 else 3) and all(r['completed'] for r in rows)
    assert len(rows)==len(samples)==len(native['weapon_samples'])
    assert all(r['receipts'][0]['handle']==[3,10,1] and r['receipts'][0]['delivered'] for r in rows)
    values=[r['modifier'] for r in samples]
    assert any(v>0 for v in values)==c['modifier_active'],values
    assert set(values)==({150.} if c['modifier_active'] else {0.})
    assert len(native['healing'])==(27 if c['duration']==30 else 0)
    assert sum(r['after']>r['before'] for r in native['healing'])==(10 if c['duration']==30 else 0)
    assert native['typed']['finished'] and not native['typed']['state'][0]['alive']
    return dict(verified=True,reference_model_gap=True,declared_model=True,original_profile=c['profile'],original_effects=c['own_effects'],complete_roster_effects=c['all_effects'],typed_packets=len(rows),positive_modifier_samples=sum(v>0 for v in values),positive_heal_deliveries=sum(r['after']>r['before'] for r in native['healing']),full_character_verified=False,in_game_rules_verified=False)
