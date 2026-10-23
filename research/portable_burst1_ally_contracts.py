"""Live stages include down allies but exclude the caster; literal HP witness."""
def verify(case,native):
    contract=case['contract'];rows=native['burst1_ally_conditions']
    assert [r['result'] for r in rows]==contract['results'],(case['name'],rows,contract)
    for r in rows:
        assert r['owner']==contract['owner'] and r['conditions']==[contract['condition']]
        has=any(stage=='1' for i,stage in enumerate(r['stages']) if i!=r['owner'])
        assert r['result']==(has if contract['condition']=='has_burst1_ally' else not has)
    assert native['allies'][contract['owner']]['hp']==contract['hp'],(case['name'],native['allies'],contract)
    if 'down-other' in case['name']:assert all(1 in r['down'] for r in rows)
    return dict(verified=True,reference_model_gap=False,checks=len(rows),results=contract['results'],hp=contract['hp'])
