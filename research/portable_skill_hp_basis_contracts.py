"""Literal damage, maximum-HP lookup, grouping and multi-hit snapshot contracts."""
def verify(case,native):
    expected=case['contract'];queries=native['skill_hp_basis_queries']
    assert native['damage']==expected['damage'],(case['name'],'totals',native['damage'])
    packets=[e for e in native['parts_skill_events'] if e['kind']=='packet']
    assert [e['damage'] for e in packets]==expected['packets'],(case['name'],'packets',packets)
    assert [q['maximum'] for q in queries]==expected['basis_maxima'],(case['name'],'maximum lookups',queries)
    assert all(q['owner']==expected['owner'] for q in queries),(case['name'],'basis owner',queries)
    assert all(q['time'] in [p['time'] for p in packets] for q in queries),(case['name'],'basis time',queries)
    if 'hp' in expected:assert [a['hp'] for a in native['allies']]==expected['hp'],(case['name'],'life heal',[a['hp'] for a in native['allies']])
    return dict(verified=True,reference_model_gap=bool(expected.get('reference_model_gap')),packets=len(packets),basis_queries=len(queries))
