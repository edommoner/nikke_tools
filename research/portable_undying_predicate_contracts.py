"""Explicit live-marker outcomes, source order, carriers and physical damage."""


def verify(case,native):
    expected=case['contract'];owner=expected['owner'];obs=native['undying_predicate'];checks=obs['checks']
    assert [r['result'] for r in checks]==expected['results'],(case['name'],'condition outcomes')
    assert [[q['result'] for q in r['queries']] for r in checks]==expected['queries'],(case['name'],'live stat outcomes')
    assert obs['carriers']==([dict(owner=owner,stack=expected['stack'])] if expected['stack'] else []),(case['name'],'retained witness')
    shots=[s for s in native['projectile_shots'] if s['owner']==owner]
    assert len(native['projectile_shots'])==len(shots)==len(checks)==3,(case['name'],'physical source')
    assert [r['time'] for r in checks]==[s['time'] for s in shots],(case['name'],'activation time')
    assert all(r['owner']==owner for r in checks),(case['name'],'caster')
    assert all(q['owner']==owner and q['stat']=='undying' and q['time']==r['time'] for r in checks for q in r['queries']),(case['name'],'live query scope')
    assert [s['damage'] for s in shots]==expected['damage'],(case['name'],'physical damage')
    assert native['damage']==[sum(expected['damage']) if i==owner else 0 for i in range(5)],(case['name'],'total damage')
    assert native['ammo'][owner]==expected['ammo'],(case['name'],'physical ammo')
    return dict(verified=True,reference_model_gap=False,condition_checks=len(checks),live_queries=sum(len(r['queries']) for r in checks),activations=sum(r['result'] for r in checks),physical_shots=len(shots))
