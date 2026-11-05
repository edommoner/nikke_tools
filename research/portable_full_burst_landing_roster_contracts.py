"""Actual original six-hit branch; the thirteen-hit branch is synthetic elsewhere."""
def verify(case,native):
    o=native['full_burst_landing'];calls=o['calls'];hits=o['hits']
    assert not o['count_reads']
    if case['contract']['duration']==3:assert not calls and not hits
    else:
        assert len(calls)==2 and len(hits)==6
        cast,land=calls;assert cast['name']==land['name']=='13 고스트' and cast['owner']==land['owner']==0
        assert not cast['full'] and not cast['resolved'] and cast['latched'] is None
        assert land['full'] and land['resolved'] and land['latched']==6 and land['excluded']==[]
        assert abs(cast['time']-253/60)<1e-12 and abs(land['time']-276/60)<1e-12
        assert all(r==dict(name='13 고스트',time=land['time'],owner=0,full=True) for r in hits)
    return dict(verified=True,reference_model_gap=False,original_definitions=True,handler_calls=len(calls),notifications=len(hits),original_six_hit_branch_verified=bool(hits),original_thirteen_hit_branch_verified=False,shots=len(native['projectile_shots']))
