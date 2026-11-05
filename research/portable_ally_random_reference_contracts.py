"""Literal pool, native sample order and integer PRNG advancement contracts."""


def verify(case,native):
    expected=case['contract'];obs=native['ally_random_reference'];samples=obs['samples'];resolutions=obs['resolutions']
    for field,key in [('pool','pools'),('picked','picked'),('k','ks'),('before_index','before'),('after_index','after')]:
        assert [r[field] for r in samples]==expected[key],(case['name'],field)
    assert resolutions==[dict(target=expected['target'],caster=expected['caster'],picked=p) for p in expected['picked']],(case['name'],'native resolutions/cache reuse')
    for index,r in enumerate(samples):
        assert len(set(r['picked']))==len(r['picked'])==r['k'] and all(n in r['pool'] for n in r['picked']),(case['name'],'sampling without replacement')
        if r['k']==0:assert r['before_sha256']==r['after_sha256'],(case['name'],'empty pool must not advance RNG')
        else:assert r['before_sha256']!=r['after_sha256'],(case['name'],'singleton/full pool still consume RNG')
        if index:assert r['before_sha256']==samples[index-1]['after_sha256'],(case['name'],'single friendly stream')
    assert native['rng']['draws']==expected['boss_draws'],(case['name'],'independent boss RNG')
    return dict(verified=True,reference_model_gap=False,sample_calls=len(samples),resolutions=len(resolutions),selected=sum(r['k'] for r in samples),global_rng_index_advance_mod624=sum((r['after_index']-r['before_index'])%624 for r in samples),boss_rng_words=native['rng']['draws'])
