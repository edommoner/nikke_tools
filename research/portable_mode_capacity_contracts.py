"""Literal memo, absence/zero, owner, firing and exit contracts."""
import math

def verify(case,native):
    expected=case['contract'];obs=native['mode_capacity'];owner=expected['owner']
    queries=[q for q in obs['queries'] if q['owner']==owner and q['reference_mode']]
    values=[]
    for q in queries:
        if not values or q['value']!=values[-1]:values.append(q['value'])
    assert values==expected['capacities'],(case['name'],'capacities',values)
    refs=[r for r in obs['references'] if r['owner']==owner]
    assert len(refs)==expected['ref_calls'],(case['name'],'reference reads',refs)
    frames=[f for f in obs['frames'] if f['owner']==owner]
    assert sum(f['hits'] for f in frames)==expected['mode_packets'],(case['name'],'mode packets',sum(f['hits'] for f in frames))
    assert sum(f['owner']==owner and f['mode_session'] and f['hits']>0 for f in obs['fires'])==expected['mode_shots'],(case['name'],'mode shots')
    exits=[f['time'] for f in frames if f['after']['restored']]
    assert len(exits)==expected['exit_count'],(case['name'],'exit count',exits)
    if expected['exit_time'] is not None:
        assert exits and math.isclose(exits[-1],expected['exit_time'],abs_tol=1e-12),(case['name'],'exit',exits)
    return dict(verified=True,reference_model_gap=False,capacity_sequence=values,reference_reads=len(refs),mode_hits=expected['mode_shots'])
