"""Literal damage/rate snapshots, caster identity and stack-bypass witnesses."""
def verify(case,native):
    expected=case['contract'];obs=native['lost_hp_attack'];samples=obs['samples']
    assert native['damage']==expected['damage'],(case['name'],'totals',native['damage'])
    assert [p['damage'] for p in native['parts_skill_events'] if p['kind']=='packet']==expected['packets'],(case['name'],'packets',native['parts_skill_events'])
    assert [p['atk_pct'] for p in samples]==expected['rates'],(case['name'],'ATK samples',samples)
    assert [p['hp_pct'] for p in samples]==expected['hp_rates'],(case['name'],'HP samples',samples)
    assert [p['name'] for p in samples]==expected['sample_names'],(case['name'],'source names',samples)
    packet_times=[p['time'] for p in native['parts_skill_events'] if p['kind']=='packet']
    assert all(p['time'] in packet_times for p in samples),(case['name'],'sample time',samples)
    assert all(p['owner']==expected['owner'] for p in samples),(case['name'],'owner',samples)
    if expected.get('scalar_absent'):assert not obs['values'],(case['name'],'absent carrier queried',obs['values'])
    else:assert obs['values'] and all(p['owner']==expected['owner'] for p in obs['values']),(case['name'],'scalar owner',obs['values'])
    assert all(p['value'] in expected['scalar_values'] for p in obs['values']),(case['name'],'scalar values',obs['values'])
    if 'max_observed_stack' in expected:
        assert max(p['stack'] for p in obs['values'])==expected['max_observed_stack'],(case['name'],'stack witness',obs['values'])
        assert all(p['value']==50 for p in obs['values']),(case['name'],'stack multiplier applied',obs['values'])
    if 'physical_packets' in expected:
        assert [p['damage'] for p in native['projectile_shots']]==expected['physical_packets'],(case['name'],'physical packets',native['projectile_shots'])
    if 'owner_hp' in expected:
        owner=native['allies'][expected['owner']]
        assert owner['hp']==expected['owner_hp'] and owner['down']==expected['owner_down'],(case['name'],'revived body',owner)
    return dict(verified=True,samples=len(samples),scalar_queries=len(obs['values']),reference_model_gap=False)
