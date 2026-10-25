"""Sample/crit draw order, actual canonical packet routing and final MT state."""
import random
def verify(case,native):
    assert native['reference_kind']=='deterministic-common-cpu'
    points=native['sampled_points'];pellets=native['physical_pellets'];assert points and len(points)==len(pellets)
    from portable_coordinate_sample_v1 import sample
    rng=random.Random(case['seed']);words=0;observed_points=0
    for draw in native['sampled_draws']:
        assert draw['rng_before_index']==rng.getstate()[1][-1]
        if draw['kind']=='point':
            expected=sample(*draw['aim'],draw['radius'],rng,angle=draw['angle'],k=draw['k'])
            assert list(expected)==draw['point'];count=4 if draw['angle'] else 2
            assert draw['rng_words']==count;words+=count;observed_points+=1
        else:
            assert draw['kind']=='native-uniform' and rng.random()==draw['value'];words+=2
        assert draw['rng_after_index']==rng.getstate()[1][-1]
    assert observed_points==len(points)
    for p,row in zip(points,pellets,strict=True):
        assert not row['expected'] and p['aim']==row['aim'] and p['radius']==row['spread_radius']
        if row['grow']>0:assert all(e['is_crit']==row['packets'][0]['is_crit'] for e in row['packets'])
        else:assert len(row['packets'])==1 and not row['packets'][0]['extra']
    state=rng.getstate()[1];assert native['physical_rng']==dict(index=state[-1],state=list(state[:-1]))
    label=case['name'].rsplit('/',1)[1]
    if label in ('body-without-targets','core-centered'):assert all(not p['angle'] for p in points)
    if label in ('core-offset','rotated-rectangle'):assert all(p['angle'] for p in points)
    if label=='full-front':assert all(r['packets'][0]['target']=='front' for r in pellets)
    if label=='interrupt-front':assert all(r['packets'][0]['target']=='stop' for r in pellets)
    return dict(verified=True,reference_model_gap=False,reference_kind='deterministic-common-cpu',pellets=len(pellets),packets=sum(len(r['packets']) for r in pellets),physical_rng_words=words,gpu_supported=False)
