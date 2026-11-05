"""No firing within3s is a control, natural30s is a positive CPU witness."""


def verify(case,native):
    obs=native['accuracy_predicate_roster'];rows=obs['checks'];expected=case['contract'];owner=case['body']['squad'].index(case['character'])
    assert len(rows)==expected['checks'],(case['name'],'condition checks')
    assert sum(r['result'] for r in rows)==expected['activations'],(case['name'],'activation count')
    assert sum(len(r['queries']) for r in rows)==expected['queries'],(case['name'],'native query count')
    assert all(r['owner']==owner for r in rows),(case['name'],'owner')
    assert all(q['owner']==owner and q['target']=='__enemy__' and q['time']==r['time'] for r in rows for q in r['queries']),(case['name'],'actual native accuracy')
    assert [[q['value'] for q in r['queries']] for r in rows]==[[v] for v in expected['values']],(case['name'],'ordered accuracy values')
    assert obs['physical_shots']==expected['shots'],(case['name'],'full physical history count')
    return dict(verified=True,reference_model_gap=False,condition_checks=len(rows),stat_queries=sum(len(r['queries']) for r in rows),activations=sum(r['result'] for r in rows),physical_shots=obs['physical_shots'],gpu_supported=False)
