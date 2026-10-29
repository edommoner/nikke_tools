"""Native movement source contract, not default or game admission."""
from enemy_movement_model import integrate


def verify(case,native):
    identity=native['original_input_identity'];data=native['enemy_movement'];rules={r['label']:r for r in case['enemy_movement']['actors']}
    assert identity['effects_owners_weapons_chars_config_seed_verified'] and identity['added_effects']==0
    assert data['frames'] and data['generations']
    active=[];moved=0
    for frame in data['frames']:
        rule=rules[frame['label']]
        for segment in frame['segments']:
            expected=integrate(segment['before'],rule['velocity'],rule['force_center'],segment['end']-segment['start'],segment['disabled'],segment['forced'],data['policies']['precedence'])
            assert expected==segment['after']
            moved+=int(segment['before']!=segment['after'])
            for field in segment['fields']:
                assert field['activated_at']<=segment['start']<field['expires_at']
                active.append((field,segment,frame['label']))
        if frame['segments']:assert frame['position']==frame['segments'][-1]['after']
    assert moved and native['logical_packets'],'Movement must reach the actual sampled shot/landing executor'
    stat='force_move' if case['contract']['scenario']=='force' else 'enemy_movement_disable'
    own=[(field,segment,label) for field,segment,label in active if field['caster']==case['contract']['owner'] and field['stat']==stat]
    assert own,'The original burst duration effect must be consumed, not replaced by an authored command'
    for field,segment,label in own:
        assert field['expires_at']==field['activated_at']+(2. if stat=='force_move' else 5.)
        if stat=='enemy_movement_disable' and not (segment['forced'] and data['policies']['precedence']=='force-before-disable'):assert segment['before']==segment['after']
        else:assert segment['after']==rules[label]['force_center']
    if case['contract']['scenario']=='renewal':assert max(r['actor'][2] for r in data['generations'])==3
    if case['contract']['scenario'].startswith('overlap'):assert any(s['disabled'] and s['forced'] for f in data['frames'] for s in f['segments'])
    return dict(verified=True,reference_model_gap=True,original_definitions=identity['definitions'],original_movement_stat=stat,
        real_duration_carriers=True,real_actor_generations=True,existing_shot_and_landing_executor=True,
        frames=len(data['frames']),generations=len(data['generations']),active_segments=len(own),moving_segments=moved,
        recipient_policy=data['policies']['recipient_policy'],gpu_wire_connected=False,gpu_supported=False,
        default_path_installed=False,in_game_motion_policy_verified=False,full_character_verified=False)
