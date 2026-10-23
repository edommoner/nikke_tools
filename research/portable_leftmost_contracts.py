"""Literal selection contracts plus full unmodified battle/trace verification."""
def verify(case,native):
    actual=native['leftmost_selections'];expected=case['contract']['picked']
    assert [r['picked'] for r in actual]==expected,(case['name'],actual,expected)
    assert all(r['owner']==0 and r['target']==case['effects'][-1]['target'] for r in actual)
    assert all(len(p)==len(set(p)) and p==sorted(p) for p in expected)
    return dict(verified=True,reference_model_gap=False,selections=len(actual),picked=expected)
