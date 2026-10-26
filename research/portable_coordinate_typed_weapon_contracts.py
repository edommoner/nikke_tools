"""Physical identity, scalar, frozen shot, routing and native RNG contracts."""
def verify(case,native):
    if 'original_run' not in case:
        from portable_coordinate_typed_weapon_cases import prepare
        case,_=prepare(case)
    from portable_coordinate_sampling_contracts import verify as sampling
    result=sampling(case,native);typed=native['coordinate_typed_weapon'];attacks=typed['attacks'];names=case['names']
    # Bind packets through the actual labels retained in the snapshot, rather
    # than assuming a wire label convention.
    labels={r['label'] for shot in typed['shots'] for r in shot['targets'] if r['handle'] is not None}
    physical=[(row,p) for row in native['physical_pellets'] for p in row['packets'] if p['target'] in labels]
    assert len(physical)==len(attacks)==len(typed['modifier_samples'])
    for i,((row,packet),attack,scalar) in enumerate(zip(physical,attacks,typed['modifier_samples'],strict=True)):
        assert attack['attack_id']==2**23+i+1 and attack['completed']
        assert attack['owner']==names.index(row['owner']) and attack['time']==row['time']
        assert attack['damage']==packet['damage']==scalar['damage']
        assert attack['critical']==packet['is_crit'] and attack['extra']==packet['extra'] and attack['hit_tag']==packet['hit_tag']
        assert len(attack['receipts'])==1
        receipt=attack['receipts'][0];assert scalar['scalar_kind']==receipt['handle'][0]
        shot=typed['shots'][attack['shot_identity']-1]
        selected=[r for r in shot['targets'] if r['label']==packet['target']]
        assert len(selected)==1 and selected[0]['handle']==receipt['handle']
    # The ordinary BODY/PART landing observer must not see typed recipients.
    assert all(p.get('target') not in labels for p in native['landed_packets'])
    label=case['name'].rsplit('/',1)[1]
    if label=='projectile-miss':assert not attacks and native['physical_pellets']
    elif label=='canonical-front':
        assert all(p['target']=='front-part' for row in native['physical_pellets'] if not row['grow'] for p in row['packets'])
    else:assert attacks and any(r['receipts'][0]['delivered'] for r in attacks)
    assert all(r['landed_same_shot']==0 for r in typed['full_charge_boundaries']),'Physical typed landing must follow full-charge notification'
    if label in ('projectile-front','shield-front','projectile-mixed-reach'):
        assert native['full_charge_quantities'] and typed['full_charge_boundaries']
        assert any(row['grow']>0 for row in native['physical_pellets']),'Original RL must actually fire'
        assert any(r['modifier']>0 for r in typed['modifier_samples']),'Original modifier must contribute'
    if label=='projectile-mixed-reach':
        assert any(not p['target'] for row in native['physical_pellets'] for p in row['packets']) and attacks
        assert any(r['extra'] for r in attacks),'Typed reach packets must be observed'
    if label=='shotgun-frozen-generation':
        by_shot={}
        for row in attacks:by_shot.setdefault(row['shot_identity'],[]).append(row)
        multi=[rows for rows in by_shot.values() if len(rows)>1]
        assert multi and any(not r['receipts'][0]['delivered'] for rows in multi for r in rows[1:]),'Later pellets retain the destroyed generation'
        assert any(r['receipts'][0]['handle'][1]==11 and r['receipts'][0]['delivered'] for r in attacks),'A later shot must reselect the back actor'
    if label=='shield-stream-overflow':assert len(attacks)>2048,'Whole-stream proof must exceed retained raw capacity'
    return dict(result,typed_attacks=len(attacks),typed_shots=len(typed['shots']),gpu_supported=False,in_game_rules_verified=False)
