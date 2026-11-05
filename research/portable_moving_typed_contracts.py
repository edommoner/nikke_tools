"""Whole native composition, retaining every source effect and group observer."""
def verify(case,native,*,require_typed_attacks=True):
    if 'original_run' not in case:
        from portable_moving_typed_cases import prepare
        case=prepare(case)[0]
    identity=native['original_input_identity'];motion=native['enemy_movement'];attachment=native['typed_attachments']
    assert identity['chars_config_seed_weapon_verified']
    original=case['original_run']['prepared']['effects']
    assert case['effects']==[r['effect'] for r in original]
    assert [case['names'][i] for i in case['owners']]==[r['owner'] for r in original]
    assert identity['definitions']==len(original) and case['duration']==30
    assert motion['frames'] and motion['generations'] and native['logical_geometry']['packets']
    assert native['physical_pellets']
    assert bool(native['coordinate_typed_weapon']['attacks'])==require_typed_attacks
    assert case['sampled_groups'] and all(k in native for k in ('groups','group_shots','group_notices','group_receipts','group_children','group_child_landings')),'Complete common group observer must remain enabled'
    frames={(f['time'],f['label']):f for f in motion['frames']}
    initial={r['label']:r['shape'] for r in case['logical_geometry']}
    links={r['typed_label']:r['actor_label'] for r in case['typed_attachment']['bindings']}
    seen=set();visible=hidden=0
    for q in attachment['queries']:
        actor=links[q['typed_label']];f=frames[q['time'],actor]
        # Position is frame-frozen; a previous packet may retire its owner in
        # this same frame before the next physical snapshot is captured.
        assert q['observed_owner']==f['actor']
        alive=q['observed_owner_alive'] and q['observed_owner']==q['owner'];assert q['visible']==alive
        if not f['alive']:assert not q['observed_owner_alive']
        if not alive:assert q['position'] is None;hidden+=1;continue
        binding=case['typed_bindings'][q['typed_slot']];assert binding['owner']==q['owner']
        shape=case['typed_geometry']['shapes'][q['typed_slot']];origin=initial[actor]
        assert q['position']==[shape['x']+(f['position'][0]-origin['x']),shape['y']+(f['position'][1]-origin['y'])]
        visible+=1;seen.add(tuple(q['position']))
    assert visible and len(seen)>1,'Physical targets must consume actual moving positions'
    if case['contract']['scenario']=='renewal':assert hidden and max(f['actor'][2] for f in motion['frames'])==3
    if case['name'].endswith('/owner-death'):assert hidden and any(not f['alive'] for f in motion['frames'])
    return dict(verified=True,reference_model_gap=True,original_definitions=identity['definitions'],duration=30,
        shared_clock_and_actor_registry=True,shared_canonical_pellet=True,logical_and_typed_packets=require_typed_attacks,
        complete_group_observer=True,group_rows=len(native['groups']),frames=len(motion['frames']),attachment_queries=len(attachment['queries']),
        visible_queries=visible,hidden_queries=hidden,distinct_positions=len(seen),
        attachment_policy=attachment['policy']['mode'],retarget_stale_owner=False,
        gpu_supported=False,gpu_wire_connected=False,default_path_installed=False,
        in_game_attachment_policy_verified=False,full_character_verified=False)
