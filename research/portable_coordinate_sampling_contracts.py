"""Sample/crit draw order, actual canonical packet routing and final MT state."""
import random
def verify(case,native):
    assert native['reference_kind']=='deterministic-common-cpu'
    points=native['sampled_points'];pellets=native['physical_pellets'];assert points and len(points)==len(pellets)
    rng=random.Random(case['seed']);words=0
    for p,row in zip(points,pellets,strict=True):
        assert not row['expected'] and p['aim']==row['aim'] and p['radius']==row['spread_radius']
        assert p['rng_before_index']==rng.getstate()[1][-1]
        rng.random();words+=2
        if p['angle']:rng.random();words+=2
        assert p['rng_words']==(4 if p['angle'] else 2) and p['rng_after_index']==rng.getstate()[1][-1]
        rng.random();words+=2 # Canonical damage draws once even at 0%/100% crit.
        if row['grow']>0:assert all(e['is_crit']==row['packets'][0]['is_crit'] for e in row['packets'])
        else:assert len(row['packets'])==1 and not row['packets'][0]['extra']
    state=rng.getstate()[1];assert native['physical_rng']==dict(index=state[-1],state=list(state[:-1]))
    label=case['name'].rsplit('/',1)[1]
    if label in ('body-without-targets','core-centered'):assert all(not p['angle'] for p in points)
    if label in ('core-offset','rotated-rectangle'):assert all(p['angle'] for p in points)
    if label=='full-front':assert all(r['packets'][0]['target']=='front' for r in pellets)
    if label=='interrupt-front':assert all(r['packets'][0]['target']=='stop' for r in pellets)
    return dict(verified=True,reference_model_gap=False,reference_kind='deterministic-common-cpu',pellets=len(pellets),packets=sum(len(r['packets']) for r in pellets),physical_rng_words=words,gpu_supported=False)
