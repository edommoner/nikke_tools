"""Literal membership transitions plus an independent Python MT stream."""
import hashlib,json,random


def verify(case,native):
    c=case['contract'];o=native['random_cleanse'];calls=o['calls'];samples=o['samples']
    assert len(calls)==len(samples)==3
    assert [r['pool'] for r in samples]==c['pools']
    assert [r['picked'] for r in samples]==c['picked']
    assert [r['before'] for r in calls]==c['before'],(case['name'],'before',calls)
    assert [r['after'] for r in calls]==c['after'],(case['name'],'after',calls)
    assert [r['down'] for r in calls]==c['down'],(case['name'],'down',calls)
    assert [r['owner'] for r in calls]==[c['owner']]*3
    rng=random.Random(case['seed']);digest=lambda state:hashlib.sha256(json.dumps(state,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    for i,(r,s) in enumerate(zip(calls,samples,strict=True)):
        assert abs(r['time']-[0,7/60,13/60][i])<1e-12
        before=rng.getstate();picked=rng.sample(c['pools'][i],min(c.get('count',2),len(c['pools'][i])));after=rng.getstate()
        assert picked==c['picked'][i] and s['k']==len(picked)
        assert s['before_sha256']==digest(before) and s['after_sha256']==digest(after)
        assert s['state_changed']==(before!=after)
        assert (s['before_index'],s['after_index'])==(before[1][-1],after[1][-1])
    assert native['rng']['draws']==0
    return dict(verified=True,reference_model_gap=False,dispatches=3,samples=3,selected=sum(map(len,c['picked'])))
