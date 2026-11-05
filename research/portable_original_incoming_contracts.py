"""Require actual incoming, recovery and protection witnesses, without scheduling."""
def verify(case,native):
    witness=case['catalogue_profile'].get('scene_witness')
    if not witness:return
    hits=native['battle']['hits']
    assert not any(h['down'] for h in hits),'Incoming witness must retain the original active roster'
    if witness['family']=='Red-Hood':
        assert len(hits)==3 and all(abs(h['time']-t)<1/60+1e-9 for h,t in zip(hits,(1.,4.,14.),strict=True)),'Incoming events must occur at their literal frame boundaries'
        assert [h['owner'] for h in hits]==([2,0,2] if witness['scenario']=='B2' else [2,2,2]),'Actual original B2 must redirect the middle attack only'
        assert all(h['hp']>0 for h in hits),'Piercing incoming attacks must actually injure targets'
        if witness['scenario']=='B2':
            heals=[h for h in native['sampled_health_returns'] if h['kind']=='_apply_lifesteal' and 4.<h['time']<12.]
            assert any(h['hp'][0]>hits[1]['hp_after'] for h in heals),'Original B2 lifesteal must actually restore injured HP'
    elif witness['family']=='Cinderella':
        assert len(hits)==3 and all(h['owner']==0 for h in hits)
        assert hits[0]['decoy']>0,'Original decoy must absorb a real attack'
        if witness['scenario']=='chipped':
            assert all(h['decoy']>0 and h['hp']==0 for h in hits),'An intact decoy must absorb each attack'
        else:
            # Canonical decoy ends the entire absorbed hit; excess does not
            # overflow into HP. Only the next hit reaches HP after exhaustion.
            assert hits[0]['damage']>hits[0]['decoy'] and hits[0]['hp']==0 and hits[1]['decoy']==0 and hits[1]['hp']>0,('After real decoy exhaustion the next attack must reach original HP',hits)
            assert hits[2]['decoy']>0 and hits[2]['hp']==0,'Original burst must restore a decoy for the later real attack'
    elif witness['family']=='Original-support':
        from portable_original_support_contracts import verify as support_verify
        support_verify(case,native)
    elif witness['family']=='Original-threshold':
        from portable_original_threshold_contracts import verify as threshold_verify
        threshold_verify(case,native)
    elif witness['family']=='Original-probability':
        from portable_original_probability_contracts import verify as probability_verify
        probability_verify(case,native)
    else:raise AssertionError('Unknown original incoming witness')
