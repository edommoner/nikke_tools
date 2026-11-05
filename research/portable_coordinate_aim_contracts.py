"""Literal arbitration/lifetime witnesses and common frame-consumer invariants."""
from timer_registry_cases import NAMES


def verify(case, native):
    observed = native['coordinate_aim']
    frames = observed['frames']
    assert frames and native['reference_kind'] == 'deterministic-common-cpu'
    assert all(a['time'] < b['time'] for a, b in zip(frames, frames[1:]))
    by_time = {f['time']: f for f in frames}
    for frame in frames:
        for aim in frame['aims']:
            assert aim['point'] == frame['centers'].get(aim['target'], frame['auto'])
    for query in observed['queries']:
        assert query['time'] in by_time, ('Missing frame', query)
        assert query['point'] == (query['selected_point'] if query['selected_point'] is not None else query['fallback_auto'])
        if query['caller'] == '_coord_pellet':
            assert query['last_resolved_frame'] == query['time']
            assert query['point'] == by_time[query['time']]['aims'][query['who']]['point']
    for pellet in native['physical_pellets']:
        assert pellet['aim'] == by_time[pellet['time']]['aims'][NAMES.index(pellet['owner'])]['point']
    for row in observed['windows']:
        e = row['entry']; gate = e.get('gate')
        eligible = not gate or gate['burst_user'] in row['users'].get(str(gate['burst_stage']), [])
        if 'window' in e:
            expected = eligible and dict(always=True, burst_charge=row['charging'],
                burst_chain=not row['charging'] and not row['full_burst'],
                own_full_burst=row['full_burst'] and bool(row['cast_mask'] & (1 << row['who'])))[e['window']]
        else:
            resolved = [a for a in observed['anchors'] if a['time'] == row['time'] and a['who'] == row['who'] and a['entry'] == e]
            value = resolved[-1]['resolved'] if resolved else None
            expected = eligible and value is not None and value[1] <= row['time'] < value[1] + e['len']
        assert row['opened'] == expected, (case['name'], row)
    label = case['name'].split('/')[-1]
    targets = lambda who: [f['aims'][who]['target'] for f in frames]
    if label == 'manual-owner-only':
        assert set(targets(0)) == {'front'} and set(targets(1)) == {''}
        assert all(f['owner'] == 0 for f in frames)
    elif label == 'first-live-entry':
        assert targets(0)[0] == 'behind' and targets(0)[-1] == 'front'
    elif label == 'target-expires':
        assert targets(0)[0] == 'front' and targets(0)[-1] == ''
    elif label == 'core-expires-fallback':
        assert targets(0)[0] == 'core' and targets(0)[-1] == 'behind'
    elif label == 'core-changes-manual-stays':
        assert set(targets(0)) == {'front'}
        assert frames[-1]['aims'][1]['point'] == [-10., 3.]
    elif label == 'priority-preemption':
        assert all(f['owner'] == 1 for f in frames)
        assert set(targets(0)) == {''} and set(targets(1)) == {'behind'}
    elif label == 'equal-priority-new-edge':
        owners = [f['owner'] for i, f in enumerate(frames) if i == 0 or frames[i-1]['owner'] != f['owner']]
        assert owners == [0, 1, 0], owners
        assert any(q['caller'] == '_coord_skill_hits' and q['last_resolved_frame'] < q['time']
                   and q['point'] != by_time[q['time']]['aims'][q['who']]['point']
                   for q in observed['queries']), 'Prior-frame skill aim must remain observable'
    elif label == 'warn-all-own':
        assert set(targets(0)) == {'front'} and set(targets(1)) == {'behind'}
    elif label in ('layer2-interrupt', 'shared-camera-layer2'):
        assert set(targets(0)) == {'stop'} and set(targets(2)) == {''}
        if label.startswith('shared'):
            assert set(targets(1)) == {'stop'}
    elif label == 'layer1-ignores-interrupt':
        assert all(set(targets(who)) == {''} for who in range(5))
    elif label == 'focus-zero-marker-expires':
        assert targets(1)[0] == 'front' and targets(1)[-1] == ''
    elif label == 'full-burst-follow':
        assert any(f['full_burst'] for f in frames)
        assert all(f['aims'][1]['target'] == ('front' if f['full_burst'] else '') for f in frames)
    elif label == 'gate-False':
        assert not any(w['opened'] for w in observed['windows']) and set(targets(0)) == {''}
    elif label == 'same-frame-target-break':
        assert targets(0)[0] == 'front' and targets(0)[-1] == ''
        pellets = native['physical_pellets']
        assert any(p['owner'] == NAMES[3] and p['time'] == frames[0]['time'] and p['aim'] == [0., 0.] for p in pellets)
    elif label == 'default-interrupt-priority':
        assert frames[0]['owner'] == 1 and frames[-1]['owner'] == 0
        requests = [r['request'] for r in observed['requests'] if r['time'] == frames[0]['time'] and r['request'] is not None]
        assert [r[1] for r in requests] == [20, 30]
    elif label == 'shared-camera-manual':
        assert all(f['aims'][0]['target'] == f['aims'][2]['target'] == 'front' and f['aims'][1]['target'] == 'behind' for f in frames)
    elif label == 'forced-camera-sequence':
        assert all(f['owner'] == 1 for f in frames)
        assert set(targets(0)) == {''} and set(targets(1)) == {'behind'}
    elif label == 'dynamic-reload-minus':
        changes = [w['resolved'][1] for w in observed['anchors'] if w['resolved'] is not None]
        assert len(set(changes)) >= 2
        assert set(targets(0)) == {'', 'front'}
    elif label.startswith(('window-', 'anchor-', 'combat-start-', 'gate-')):
        assert any(w['opened'] for w in observed['windows']), label
        if label == 'anchor-next-fb-prediction':
            assert not observed['windows'][0]['opened']
            assert any(a['resolved'] is not None for a in observed['anchors'])
    else:
        raise AssertionError('Missing literal aim contract: ' + label)
    return dict(verified=True, reference_model_gap=False,
                reference_kind='deterministic-common-cpu', frame_count=len(frames),
                actual_aim_queries=len(observed['queries']), windows=len(observed['windows']),
                anchors=len(observed['anchors']), gpu_supported=False,
                shared_gpu_aim_connected=False, historical_native_equivalence=False)
