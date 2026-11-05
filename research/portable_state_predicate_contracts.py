"""Literal condition, ordered cover reads, camera transitions and damage."""


def verify(case,native):
    expected=case['contract'];owner=expected['owner'];obs=native['state_predicates'];rows=obs['checks'];runtime=obs['runtime']
    assert [r['result'] for r in rows]==expected['results'],(case['name'],'condition outcomes')
    assert [[q['owner'] for q in r['cover']] for r in rows]==expected['cover_query_owners'],(case['name'],'ordered alive cover reads')
    assert [[q['result'] for q in r['cover']] for r in rows]==expected['cover_query_values'],(case['name'],'cover liveness')
    assert all(r['owner']==owner for r in rows),(case['name'],'activation caster')
    assert len(runtime)==expected['runtime_count'],(case['name'],'runtime reads')
    transitions=[]
    for r in runtime:
        assert r['owner']==owner and r['result']==bool(r['camera_mask']&(1<<owner)),(case['name'],'camera uses caster, not recipient')
        item=[r['camera_mask'],r['result']]
        if not transitions or transitions[-1]!=item:transitions.append(item)
    assert transitions==expected['runtime_transitions'],(case['name'],'camera sequence')
    assert obs['carriers']==([dict(owner=owner,stack=expected['stack'])] if expected['stack'] else []),(case['name'],'witness carriers')
    shots=[s for s in native['projectile_shots'] if s['owner']==owner]
    assert len(native['projectile_shots'])==len(shots)==len(expected['damage']),(case['name'],'physical source')
    assert [s['damage'] for s in shots]==expected['damage'],(case['name'],'physical damage')
    assert native['damage']==[sum(expected['damage']) if i==owner else 0 for i in range(5)],(case['name'],'total damage')
    assert native['ammo'][owner]==expected['ammo'],(case['name'],'ammo')
    return dict(verified=True,reference_model_gap=False,condition_checks=len(rows),cover_queries=sum(len(r['cover']) for r in rows),runtime_queries=len(runtime),activations=sum(r['result'] for r in rows),physical_shots=len(shots))
