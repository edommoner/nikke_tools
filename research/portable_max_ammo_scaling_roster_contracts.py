"""Original full-profile recipient and live-value contract; complete battle is retained."""
def verify(case,native):
    o=native['max_ammo_scaling'];outer=[r for r in o['reads'] if not r['recursive']];inner=[r for r in o['reads'] if r['recursive']]
    assert outer and len(outer)==len(o['capacities'])
    assert all(r['value'] is None and r['owner']==0 for r in inner)
    for r,c in zip(outer,o['capacities']):
        assert r['owner']==c['owner']==0 and r['time']==c['time']
        assert r['base']==2.01 and c['value']>=6 and r['value']==2.01*c['value']
    assert len(native['projectile_shots'])>0
    return dict(verified=True,reference_model_gap=False,original_definitions=True,outer_queries=len(outer),nested_skips=len(inner),physical_shots=len(native['projectile_shots']))
