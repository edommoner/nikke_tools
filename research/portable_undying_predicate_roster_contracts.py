"""Live original marker at first burst, expiry before the second burst."""


def verify(case,native):
    obs=native['undying_predicate_roster'];rows=obs['checks'];expected=case['contract'];owner=case['body']['squad'].index(case['character'])
    assert [r['result'] for r in rows]==expected['results'],(case['name'],'activation outcomes')
    assert [[q['result'] for q in r['queries']] for r in rows]==[[v] for v in expected['results']],(case['name'],'native live marker reads')
    assert all(r['owner']==owner for r in rows),(case['name'],'condition owner')
    assert all(q['owner']==owner and q['stat']=='undying' and q['time']==r['time'] for r in rows for q in r['queries']),(case['name'],'live query scope')
    assert obs['physical_shots']==expected['shots'],(case['name'],'full physical history')
    return dict(verified=True,reference_model_gap=False,condition_checks=len(rows),live_queries=sum(len(r['queries']) for r in rows),activations=sum(r['result'] for r in rows),physical_shots=obs['physical_shots'],gpu_supported=False)
