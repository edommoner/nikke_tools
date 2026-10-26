"""Frame candidates, real arbitration, shot aim and explicit unsupported selectors."""
def verify(row,native):
    from portable_coordinate_typed_weapon_cases import prepare
    case=row if 'original_run' in row else prepare(row)[0]
    if case.get('expect_reference_gap'):
        assert native['reference_model_gap'] and native['blocked_before_first_frame']
        assert native['unhandled_selector']==case['expect_reference_gap']
        assert native['original_definitions']==len(case['effects']) and native['original_names']==case['names']
        assert any(e.get('target')==case['expect_reference_gap'] for e in case['effects'])
        return dict(verified=True,reference_model_gap=True,canonical_consumer_verified=False,gpu_supported=False,unhandled_selector=case['expect_reference_gap'])
    from portable_coordinate_typed_weapon_contracts import verify as weapon_verify
    proof=weapon_verify(case,native);frames=native['coordinate_typed_aim'];resolved=native['coordinate_aim']['frames']
    assert frames and len({f['time'] for f in frames})==len(frames)
    by_time={f['time']:f for f in frames};labels={'typed-front','typed-back'}
    for f in resolved:
        candidates=by_time[f['time']];live={c['label']:c for c in candidates['candidates']}
        for aim in f['aims']:
            if aim['target'] in labels:assert aim['target'] in live and aim['point']==live[aim['target']]['point']
        # Typed centers are an aim interface, never ordinary skill targets.
        assert not labels.intersection(f['centers'])
    label=case['typed_aim_witness']
    if label=='fallback':
        assert frames[0]['candidate']=='typed-front' and frames[-1]['candidate']==''
        for f in resolved:
            snapshot=by_time[f['time']];expected=snapshot['candidate'];point=[10000.,0.] if expected else snapshot['canonical_auto']
            assert all(a['target']==expected and a['point']==point for a in f['aims'])
    elif label=='destroy-next-frame':
        assert frames[0]['candidate']=='typed-front' and frames[1]['candidate']=='typed-back'
        assert any(f['candidate']=='' for f in frames[2:])
        assert all(a['target']=='typed-front' for a in resolved[0]['aims'])
        assert all(a['target']=='typed-back' for a in resolved[1]['aims'])
    elif label in ('manual-canonical','manual-typed'):
        target='manual-part' if label=='manual-canonical' else 'typed-back'
        assert all(f['aims'][0]['target']==target for f in resolved if target=='manual-part' or by_time[f['time']]['candidate'])
        assert any(f['aims'][1]['target']=='typed-front' for f in resolved)
    elif label=='adds-first':
        from calculator.boss_pattern import AIM_ADDS
        assert all(a['target']==AIM_ADDS for f in resolved for a in f['aims'])
    elif label=='full-burst-follow':
        before=[f for f in resolved if not f['full_burst']];during=[f for f in resolved if f['full_burst']]
        assert before and during,'Original burst gauge must actually enter full burst'
        assert any(f['aims'][1]['target']=='typed-front' for f in before)
        assert all(a['target']=='typed-back' and a['point']==[-10000.,0.] for f in during for a in f['aims'])
    else:raise AssertionError('Unverified declared typed aim witness')
    return dict(proof,verified=True,reference_model_gap=False,frame_candidates=len(frames),actual_resolved_frames=len(resolved),canonical_resolver_preserved=True,ordinary_skill_geometry_preserved=True,gpu_supported=False,canonical_consumer_verified=False)
