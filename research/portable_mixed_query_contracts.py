"""Literal native contracts for concurrent focus, numeric, heal and part consumers."""
import hashlib
import json

CONTRACTS = {'mixed-query-focus-owner': {'name': 'mixed-query-focus-owner',
                             'queries': 248,
                             'hits': 158,
                             'samples': 90,
                             'direct': 89,
                             'outside': 1,
                             'damage': [21600, 0, 0, 0, 0],
                             'shots': [7200, 7200, 7200],
                             'hp': [10000.0, 10000.0, 10000.0, 10000.0, 10000.0],
                             'heal_events': 3,
                             'share_calls': 0,
                             'parts': [3],
                             'sample_sha256': 'dc4198b94fecce3003ede975ecd47b2b9fc9c989e0e5e4fa29a7844499873fe9'},
 'mixed-query-focus-foreign': {'name': 'mixed-query-focus-foreign',
                               'queries': 248,
                               'hits': 158,
                               'samples': 90,
                               'direct': 89,
                               'outside': 1,
                               'damage': [19800, 0, 0, 0, 0],
                               'shots': [6600, 6600, 6600],
                               'hp': [10000.0, 10000.0, 10000.0, 10000.0, 10000.0],
                               'heal_events': 3,
                               'share_calls': 0,
                               'parts': [3],
                               'sample_sha256': 'dc4198b94fecce3003ede975ecd47b2b9fc9c989e0e5e4fa29a7844499873fe9'},
 'mixed-query-focus-empty': {'name': 'mixed-query-focus-empty',
                             'queries': 248,
                             'hits': 158,
                             'samples': 90,
                             'direct': 89,
                             'outside': 1,
                             'damage': [19800, 0, 0, 0, 0],
                             'shots': [6600, 6600, 6600],
                             'hp': [10000.0, 10000.0, 10000.0, 10000.0, 10000.0],
                             'heal_events': 3,
                             'share_calls': 0,
                             'parts': [3],
                             'sample_sha256': 'dc4198b94fecce3003ede975ecd47b2b9fc9c989e0e5e4fa29a7844499873fe9'},
 'mixed-query-focus-heal': {'name': 'mixed-query-focus-heal',
                            'queries': 248,
                            'hits': 155,
                            'samples': 93,
                            'direct': 92,
                            'outside': 1,
                            'damage': [20400, 0, 0, 0, 0],
                            'shots': [7200, 6600, 6600],
                            'hp': [5600.0, 5600.0, 5600.0, 5600.0, 5600.0],
                            'heal_events': 45,
                            'share_calls': 3,
                            'parts': [3],
                            'sample_sha256': 'f5d66a8482e51300317f2c50759734f0aeb73b77f84583fc849ee817aed99c18'},
 'mixed-query-focus-parts': {'name': 'mixed-query-focus-parts',
                             'queries': 257,
                             'hits': 166,
                             'samples': 90,
                             'direct': 89,
                             'outside': 1,
                             'damage': [61200, 0, 0, 0, 0],
                             'shots': [7200, 7200, 7200],
                             'hp': [10000.0, 10000.0, 10000.0, 10000.0, 10000.0],
                             'heal_events': 9,
                             'share_calls': 0,
                             'parts': [5, 0, 0],
                             'sample_sha256': '1fd6d7b017511d306e90de9bca90341290fb08c229c9b5e716ffcbc951d8c42d'},
 'mixed-query-focus-heal-parts': {'name': 'mixed-query-focus-heal-parts',
                                  'queries': 257,
                                  'hits': 163,
                                  'samples': 93,
                                  'direct': 92,
                                  'outside': 1,
                                  'damage': [60000, 0, 0, 0, 0],
                                  'shots': [7200, 6600, 6600],
                                  'hp': [5600.0, 5600.0, 5600.0, 5600.0, 5600.0],
                                  'heal_events': 51,
                                  'share_calls': 3,
                                  'parts': [5, 0, 0],
                                  'sample_sha256': '4fb669b6a63f7ee7ef7fe8fb145e6e24c299f0cfe556cea0bfb9fc067ff4ad1c'}}


def verify(case, native):
    expected=CONTRACTS[case['name']]
    queries=native['mixed_query']['queries'];samples=native['mixed_query']['samples']
    events=native['heal_share_events']
    actual=dict(name=case['name'],queries=len(queries),hits=sum(q['hit'] for q in queries),
                samples=len(samples),direct=sum(not s['lazy'] for s in samples),
                outside=sum(s['query'] is None for s in samples),damage=native['damage'],
                shots=[s['damage'] for s in native['projectile_shots']],
                hp=[a['hp'] for a in native['allies']],heal_events=len(events),
                share_calls=sum(e['kind']=='shared-call' for e in events),
                parts=[p[3] for p in native['actor_pools']['pools']],
                sample_sha256=hashlib.sha256(json.dumps(samples,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest())
    assert actual==expected,('mixed native consumer contract',actual,expected)
    for query in queries:
        if query['hit']:
            assert not query['sample_indices'] and query['before_index']==query['after_index'],'cache hit consumed RNG'
    assert native['focus_aim'],'missing pre-weapon focus observation'
    camera=0 if case['name'].endswith('empty') else 16 if case['name'].endswith('foreign') else 1
    assert all(row['camera']==camera for row in native['focus_aim']),'camera ownership'
    return dict(verified=True,reference_model_gap=False,queries=len(queries),samples=len(samples),gpu_supported=False)
