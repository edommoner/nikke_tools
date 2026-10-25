"""Real sampled CPU battle under the user-selected common coordinate math.

Only point/shape numeric providers and this private observer's mode change.
Canonical per-pellet damage, critical override, callbacks and landing run as-is.
"""
from contextlib import contextmanager
from unittest.mock import patch

@contextmanager
def common_sampling_policy(points=None,draws=None):
    import engine_worker
    from calculator import timeline,aim
    from portable_coordinate_sample_v1 import sample
    from coordinate_geometry_reference import evaluate
    original=timeline.simulate;saved=timeline.random.getstate();uniform=timeline.random.random
    def sampled_battle(*args,**kwargs):
        kwargs=dict(kwargs);kwargs['config']=dict(kwargs.get('config',{}),rng_mode='random')
        return original(*args,**kwargs)
    def provider(ax,ay,radius,rng,*,angle=True,k=aim.MODEL_N):
        before=rng.getstate()[1][-1];point=sample(ax,ay,radius,rng,angle=angle,k=k);after=rng.getstate()[1][-1]
        if points is not None:points.append(dict(aim=[ax,ay],radius=radius,angle=angle,k=k,point=list(point),rng_before_index=before,rng_after_index=after,rng_words=(after-before)%624))
        if draws is not None:draws.append(dict(kind='point',**points[-1]))
        return point
    def native_uniform():
        import sys
        before=timeline.random.getstate()[1][-1];value=uniform();after=timeline.random.getstate()[1][-1]
        if draws is not None:draws.append(dict(kind='native-uniform',value=value,rng_before_index=before,rng_after_index=after,caller=sys._getframe(1).f_code.co_name))
        return value
    def distance(shape,px,py):
        return evaluate((1 if shape.is_circle else 2,shape.x,shape.y,shape.r,shape.w,shape.h,shape.rot,px,py,0.,0.))['distance']
    try:
        with patch.object(timeline,'simulate',sampled_battle),patch.object(timeline,'sample_landing',provider),patch.object(aim.Shape,'dist',distance),patch.object(timeline.random,'random',native_uniform):yield
    finally:timeline.random.setstate(saved)

def observe(case):
    import engine_worker
    from calculator import timeline
    from world_coordinate_physical_native import observe as physical
    points=[];draws=[]
    with common_sampling_policy(points,draws):
        result=physical(case);state=timeline.random.getstate()[1]
    assert len(points)==len(result['physical_pellets']) and all(not r['expected'] for r in result['physical_pellets'])
    result.update(reference_kind='deterministic-common-cpu',contract='coordinate-sample-v1',sampled_points=points,sampled_draws=draws,physical_rng=dict(index=state[-1],state=list(state[:-1])),scope='Real canonical sampled battle under common point/shape math; CPU observation only')
    return result,result['skill_trace']
