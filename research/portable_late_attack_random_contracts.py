"""Literal CPU consumer contracts, independent of GPU membership expectations."""
import hashlib
import json

CONTRACTS = {
    'caster': (90, 89, 1, [6600]*3, '93ffadc0774cc13c7f6a60a2512b25291eefed6abc9ff52f9dd7cf348030022e'),
    'caster-hp-pass': (90, 89, 1, [6600]*3, '93ffadc0774cc13c7f6a60a2512b25291eefed6abc9ff52f9dd7cf348030022e'),
    'hp': (90, 90, 0, [7000]*3, '400095350cb3bf5d76e9ccd366d47fda1f4e7eadf0c4b656ec9f490a1dc3fa05'),
    'mapped-control': (1, 0, 0, [6000]*3, 'c067478655ccbaec6b351ade3da1e717ffc2188bcc57917c7672bd22c1936fb4'),
    'caster-mapped-sibling': (90, 89, 0, [6600, 6000, 6000], '2df41232d3ab033ad6b4fcb3bc41cc07880d2dc3c4c85f35979d389d9b5da2a2'),
    'post-hit-mutation': (93, 92, 1, [6600, 6000, 6000], '46e3c5772bb654457e2077b8cb02f3583e061580ebf3751816ec7ddbcb8ab593'),
    'expiry-log-rearm': (91,89,2,[6600,6600,6000],'b5394c62836be0d57b491eecc900fbab051349f3aa82c314eeca8552b2199bbf'),
    'expiry-log-on': (55,54,1,[6600,6600,6000],'028103ff9e83f9dfcda3b8f132551f2f039490ae4be7ffc22a960ff38a0509b1'),
    'first-capped-heal': (91,90,1,[6600,6000,6000],'0ad2f0b56411147ab1a5f78461427c28a64a1bbb8b9c66c75857ecd9df22abd5'),
    'full-burst-log-off': (385,384,1,[6600,6600,9000],'3fcc3967b6261f1149049a9ea5c496106193ec81c3b7b05e439586797348a115'),
    'full-burst-log-on': (390,389,6,[6600,6600,9000],'a6a7ac0ffd0e495b0d22d236f9320602407b5097c3e3f898b016bb7b5508cb30'),
}


def verify(case, native):
    count, direct, outside, damage, digest = CONTRACTS[case['name'].removeprefix('late-attack-random-')]
    queries = native['late_attack_random']['queries']
    samples = native['late_attack_random']['samples']
    snapshot=case['name'].startswith('late-attack-random-full-burst-log-')
    hits=697 if snapshot else {'late-attack-random-post-hit-mutation':155,'late-attack-random-first-capped-heal':157}.get(case['name'],158)
    assert len(queries) == (1082 if snapshot else 248) and sum(q['hit'] for q in queries) == hits, 'original query/cache boundaries'
    assert len(samples) == count and sum(not s['lazy'] for s in samples) == direct, 'late reads must not become lazy reads'
    assert sum(s['query'] is None for s in samples) == outside, 'out-of-query consumption'
    for q in queries:
        if q['hit']:
            assert not q['sample_indices'] and q['before_index'] == q['after_index'], 'cache hit must not consume RNG'
    for s in samples:
        assert s['k'] == 1 and s['pool'] == [0, 1, 2, 3], 'caster excluded from candidate pool'
        assert len(s['picked']) == 1 and s['picked'][0] in s['pool'], 'ordered sample membership'
    actual = hashlib.sha256(json.dumps(samples, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    assert actual == digest, 'complete query ownership, sample order and MT state'
    assert [s['damage'] for s in native['projectile_shots']] == damage, 'late-pass contribution'
    return dict(verified=True, reference_model_gap=False, queries=len(queries), cache_hits=hits,
                samples=count, direct_samples=direct, lazy_samples=count-direct,
                gpu_supported=False)
