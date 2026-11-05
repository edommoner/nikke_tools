"""Literal shot results and real provider recursion contracts before GPU admission."""
# owner shot damage, capacity set, outer/nested calls. Values are native contracts,
# not portable output or a fixture-generated calculation.
EXPECTED={
 'basic':([1350,1350],[5],64,64),
 'zero':([900,900],[5],64,64),
 'negative':([810,810],[5],64,64),
 'owner-four':([1350,1350],[5],64,64),
 'recipient-allies':([1530,1530],[3,4,5,6,7],320,320),
 'percent':([1620,1620],[8],64,64),
 'flat':([1530,1530],[7],64,64),
 'minimum-one':([990],[1],61,61),
 'separate-rounding':([1530,1530],[7],64,64),
 'grouped-rounding':([1440,1440],[6],64,64),
 'stack-two':([1080,1080],[5],64,64),
 'arrives-live':([1350,1710],[5,9],64,64),
 'expires-live':([1710,1350],[5,9],64,64),
 'one-bullet-late':([900,1710],[5,9],28,28),
 'one-bullet-start':([1350,900],[5],16,16),
 'condition-false':([900,900],[],0,0),
 'mode-fixed':([1080,1080],[2],45,0),
 'mode-buffed':([1440]*4,[6],64,1),
 'mode-latched':([1080,1080],[2,6],46,2),
 'mode-expires':([1440,1710],[6,9],65,38),
}

def verify(case,native):
    kind=case['contract']['kind'];owner=case['contract']['owner'];damage,capacities,outer_count,nested_count=EXPECTED[kind]
    o=native['max_ammo_scaling'];outer=[r for r in o['reads'] if not r['recursive']];inner=[r for r in o['reads'] if r['recursive']]
    assert (len(outer),len(inner),len(o['capacities']))==(outer_count,nested_count,outer_count),(kind,len(outer),len(inner),len(o['capacities']))
    assert all(r['value'] is None for r in inner),(kind,inner)
    assert sorted({r['value'] for r in o['capacities']})==capacities
    for read,cap in zip(outer,o['capacities']):
        assert (read['owner'],read['time'])==(cap['owner'],cap['time'])
        assert read['value']==read['base']*cap['value']
    shots=[s for s in native['projectile_shots'] if s['owner']==owner]
    assert [s['damage'] for s in shots]==damage,(kind,shots)
    expected=[1800]*5;expected[owner]=sum(damage)
    if kind=='recipient-allies':
        expected=[2340,2520,2700,2880,3060]
        assert sorted({(r['owner'],r['value']) for r in o['capacities']})==list(enumerate(range(3,8)))
    assert native['damage']==expected,(kind,native['damage'],expected)
    assert native['shots']==[len(damage) if i==owner else 2 for i in range(5)]
    if kind in ('arrives-live','expires-live','one-bullet-late'):
        early=9 if kind=='expires-live' else 5;late=5 if kind=='expires-live' else 9
        assert all(r['value']==(early if r['time']<.4 else late) for r in o['capacities'])
    if kind=='mode-latched':
        assert all(r['value']==(2 if r['time']<.76 else 6) and r['memo']==r['value'] for r in o['capacities'])
        assert any(.4<r['time']<.7 and r['value']==2 for r in o['capacities'])
    return dict(verified=True,reference_model_gap=False,outer_queries=outer_count,nested_skips=nested_count,physical_shots=len(shots),live_recipient=True)
