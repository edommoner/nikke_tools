"""Strict native defense comparison and resolution timing, not packing proof."""
def verify(case,native):
    rows=native['below_def_selections'];expected=case['contract']
    assert [r['picked'] for r in rows]==expected['picked'],(case['name'],rows,expected)
    for r in rows:
        assert r['owner']==0 and r['lazy']==expected['lazy'],(case['name'],r)
        assert [d['who'] for d in r['reads']]==[0,0,1,2,3,4],(case['name'],r)
        owner=r['reads'][0]['value'];eligible=[d['who'] for d in r['reads'][1:] if d['value']<owner]
        assert all(w in eligible for w in r['picked'])
        assert r['picked']==sorted(r['picked']) and len(set(r['picked']))==len(r['picked'])
    return dict(verified=True,reference_model_gap=False,selections=len(rows),defense_reads=sum(len(r['reads']) for r in rows),picked=expected['picked'])
