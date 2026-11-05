"""No duration/count reduction or truncated observation at maximum ADD slots."""
def verify(case,native):
    from portable_moving_group_contracts import verify as group_contract
    from portable_moving_many_cases import prepare_case
    if 'original_run' not in case:case=prepare_case(case)[0]
    result=group_contract(case,native);frames=native['enemy_movement']['frames']
    assert len(case['logical_geometry'])==len(case['enemy_movement']['actors'])==127
    assert len(frames)==1801*127 and len({tuple(f['actor']) for f in frames})==127
    assert all(f['actor'][2]==1 for f in frames)
    assert case['duration']==30 and result['original_definitions']==71
    assert {f['label'] for f in frames}=={r['label'] for r in case['logical_geometry']}
    frozen={f['label'] for f in frames for s in f['segments'] if s['disabled']}
    assert len(frozen)==127,'The real source carrier must reach every declared ADD'
    assert any(f['time']>=29.99 for f in frames)
    result.update(add_slots=127,all_actor_frames=True,all_actor_duration_carriers=True)
    return result
