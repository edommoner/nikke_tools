"""Independent MT proof includes discarded eligibility probes and zero calls."""
import hashlib,json,random

def verify(case,native):
    c=case['contract'];o=native['random_cleanse'];calls=o['calls'];samples=o['samples']
    assert len(calls)==c['dispatches']
    assert [s['pool'] for s in samples]==c['pools'] and [s['picked'] for s in samples]==c['picked']
    assert all(r['before']==r['after']==c['remaining'] and r['owner']==0 for r in calls)
    rng=random.Random(case['seed']);digest=lambda s:hashlib.sha256(json.dumps(s,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    assert o['seed_sha256']==[digest(rng.getstate())]
    for i,s in enumerate(samples):
        before=rng.getstate();picked=rng.sample(c['pools'][i],min(2,len(c['pools'][i])));after=rng.getstate()
        assert picked==s['picked'] and s['k']==len(picked)
        assert (s['before_sha256'],s['after_sha256'])==(digest(before),digest(after))
        assert (s['before_index'],s['after_index'])==(before[1][-1],after[1][-1])
    assert native['rng']['draws']==0
    return dict(verified=True,reference_model_gap=False,dispatches=len(calls),samples=len(samples),discarded_probes=len(samples)-len(calls))
