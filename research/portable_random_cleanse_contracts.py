"""Assert authored eligibility, native random order and exact carrier edits."""
def verify(case,native):
    e=case['contract'];obs=native['random_cleanse'];calls=obs['calls'];samples=obs['samples']
    assert len(calls)==len(samples)==1,(case['name'],obs)
    call=calls[0];s=samples[0]
    assert call['owner']==e['owner'] and call['time']==0
    assert s['pool']==e['pool'] and s['picked']==e['picked'] and s['k']==len(e['picked']),(case['name'],s)
    assert s['state_changed']==bool(e['picked'])
    assert s['before_index']==624
    assert s['after_index']==(624 if not e['picked'] else 2 if len(e['pool'])==1 else 5 if len(e['pool'])==4 or case['seed']==0 else 6),(case['name'],s)
    assert call['after']==e['remaining'],(case['name'],call,e)
    assert call['before']==e['before'],(case['name'],'initial memberships')
    assert call['before']['beneficial']==list(range(5))
    for key in ('locked','beneficial'):
        assert call['before'].get(key)==call['after'].get(key)
    assert native['rng']['draws']==0
    return dict(verified=True,reference_model_gap=False,dispatches=1,samples=1,selected=len(e['picked']),remaining=call['after'])
