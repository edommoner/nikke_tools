"""Native prerequisites: original AoE flags, target generation and one credit."""


def verify(case,native):
    label=case['contract']['label'];attacks=native['typed']['attacks'];packets=native['packet_samples'];samples=native['shield_samples']
    assert len(attacks)==len(packets)==len(samples)<=case['max_attacks']
    assert native['typed']['finished'] and all(r is None or not r['alive'] for r in native['typed']['state'])
    assert all(r['completed'] and len(r['receipts'])==1 and r['receipts'][0]['delivered'] for r in attacks)
    skills=[(packet,sample,attack) for packet,sample,attack in zip(packets,samples,attacks,strict=True) if packet['source'] is not None]
    aoe=[(p,s,a) for p,s,a in skills if s['family_flags']['is_aoe_burst']]
    if label in ('hp','hit','hit-then-hp','hp-then-hit'):
        assert len(aoe)==1
        packet,sample,attack=aoe[0]
        assert packet['name']=='피날레' and attack['owner']==0
        assert sample['family_flags']==dict(is_burst_damage=True,is_aoe_burst=True,is_single_burst=False)
        assert sample['modifier']==150.
        hp=label in ('hp','hit-then-hp')
        assert sample['scalar_kind']==(3 if hp else 0) and sample['applied_modifier']==(150. if hp else 0.)
        if case['contract'].get('aoe_specific_bonus'):
            assert case['contract']['aoe_specific_bonus']==435.6
            # Native factor order: ordinary20.9%, AoE435.6%, then HP-only150%.
            assert sample['factor5']==(7.0649999999999995 if hp else 5.5649999999999995)
            if hp:assert attack['damage']==5005368.
        else:
            assert sample['factor5']==(2.5 if hp else 1.)
            assert attack['damage']==(1862720. if hp else 745088.)
        receipt=attack['receipts'][0]
        assert receipt['slot']==(1 if label in ('hit-then-hp','hp-then-hit') else 0)
        assert receipt['handle']==[3 if hp else 4,11 if receipt['slot'] else 10,1]
    else:
        assert not aoe
    if label=='stale-owner':assert not attacks
    if label=='break-body':assert len(attacks)==1 and attacks[0]['receipts'][0]['broken']
    # Every hit-shield packet consumes exactly one credit even for AoE bursts
    # and separate shotgun pellets. Damage and credit remain distinct units.
    for state in native['typed']['state']:
        if state is not None and state['handle'][0]==4:
            used=sum(r['took'] for a in attacks for r in a['receipts'] if r['handle']==state['handle'])
            assert state['capacity']-state['remaining']==used
    return dict(verified=True,reference_model_gap=True,declared_model=True,positive_aoe_burst=bool(aoe),full_character_verified=False,gpu_connected=False,in_game_rules_verified=False)
