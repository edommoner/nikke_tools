"""Record actual original Cocoa dispatches; no assumption that a trigger fires."""
def verify(case,native):
    calls=native['random_cleanse']['calls'];samples=native['random_cleanse']['samples']
    assert len(samples)==len(calls)
    assert all(s['pool']==s['picked']==[] and s['k']==0 and not s['state_changed'] for s in samples)
    assert all(r['owner']==0 and r['before']==r['after'] for r in calls)
    if case['contract']['duration']==30:assert len(calls)>0
    return dict(verified=True,reference_model_gap=False,dispatches=len(calls),samples=len(samples),original_definitions=True,shots=len(native['projectile_shots']))
