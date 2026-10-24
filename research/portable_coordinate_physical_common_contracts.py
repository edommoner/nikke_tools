"""Literal packet/retirement contracts for the real expected-mode producer."""
EXPECTED = {
    'occlusion-and-body': [[('', 1957, False), ('front', 65, False)]],
    'full-front': [[('front', 3000, False)]],
    'interrupt-front': [[('stop', 2000, False)]],
    'two-muzzles-three-pellets': [[('', 653, False), ('front', 22, False)]] * 6,
    'retirement': [[('', 1957, False), ('front', 65, False)],
                   [('', 1942, False), ('behind', 87, False)],
                   [('', 1918, False), ('behind', 123, False)]],
    'body-without-targets': [[('', 2000, False)]],
    'pierce-reach': [[('', 2000, False), ('front', 3000, True), ('behind', 3000, True)]],
    'charge-pierce': [[('', 2000, False), ('front', 3000, True), ('behind', 3000, True)]],
    'threshold-snapshot': [[('front', 1000, False)]] * 6 +
                          [[('', 0, False), ('front', 7000, False)]] * 6,
}


def verify(case, native):
    assert native['reference_kind'] == 'deterministic-common-cpu'
    assert native['contract'] == 'coordinate-landing-v1'
    rows = native['physical_pellets']
    expected = EXPECTED[case['name'].split('/')[-1]]
    actual = [[(p['target'], p['damage'], p['extra']) for p in r['packets']] for r in rows]
    assert actual == expected, (case['name'], actual, expected)
    assert all(row['expected'] is True for row in rows)
    assert all(row['time'] <= after['time'] for row, after in zip(rows, rows[1:]))
    if case['name'].endswith('/full-front'):
        assert native['battle']['team_counts'] == [1, 0]
        assert native['battle']['actor_pools']['pools'][0][3] == 0
    if case['name'].endswith('/threshold-snapshot'):
        assert native['battle']['team_counts'] == [11, 0]
        assert len({row['time'] for row in rows[:6]}) == 1
        assert len({row['time'] for row in rows[6:]}) == 1
        assert rows[0]['time'] < rows[6]['time']
    for row in rows:
        assert len(row['geometry']) == len(row['landing']['front']) == len(row['landing']['reach'])
        assert all(0. <= row[k] <= 1. for k in
                   ('part_fraction', 'body_fraction', 'core_fraction', 'critical_fraction'))
    return dict(verified=True, reference_model_gap=False,
                reference_kind='deterministic-common-cpu', contract='coordinate-landing-v1',
                logical_pellets=len(rows), expanded_packets=sum(map(len, actual)),
                gpu_supported=False, historical_native_equivalence=False)
