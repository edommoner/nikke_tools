"""Literal native prerequisites for full-profile plain/burst skill routing."""
def verify(case,native):
    label=case['contract']['label'];rows=native['typed']['attacks'];packets=native['packet_samples'];samples=native['shield_samples']
    count={'early-hp':17,'hp':38,'hit':38,'break':1}[label]
    assert len(rows)==len(packets)==len(samples)==count
    assert native['typed']['finished'] and not native['typed']['state'][0]['alive']
    remaining={'early-hp':999999549032.,'hp':999943001161.,'hit':12.,'break':0.}[label]
    assert native['typed']['state'][0]['remaining']==remaining
    assert all(r['completed'] and len(r['receipts'])==1 and r['receipts'][0]['delivered'] for r in rows)
    indices=[i for i,r in enumerate(packets) if r['source'] is not None]
    assert indices==([20,23,30] if label in ('hp','hit') else [])
    if indices:
        assert [packets[i]['source'] for i in indices]==[37,1,6]
        assert [rows[i]['time'] for i in indices]==[4.116666666666657,4.133333333333324,4.216666666666657]
        expected=[748299.,4727897.,44161247.] if label=='hp' else [748299.,590618.,7703705.]
        assert [rows[i]['damage'] for i in indices]==expected
        assert [samples[i]['applied_modifier'] for i in indices]==([0.,700.5,700.5] if label=='hp' else [0.,0.,0.])
        assert samples[20]['family_flags']==dict(is_burst_damage=True,is_aoe_burst=False,is_single_burst=True)
        # Rei's original B3 definition says damage, not burst_damage. Its source
        # label alone must not turn on burst-family multipliers.
        assert samples[30]['family_flags']==dict(is_burst_damage=False,is_aoe_burst=False,is_single_burst=False)
    assert all(r['receipts'][0]['handle']==[4 if label=='hit' else 3,10,1] for r in rows)
    return dict(verified=True,reference_model_gap=True,declared_model=True,original_profile=case['contract']['profile'],original_skill_definitions=7,prepared_definitions=73,typed_packets=count,skill_packets=len(indices),original_selectors_preserved=True,burst_single_flags_observed=bool(indices),gpu_connected=False,in_game_rules_verified=False,full_character_verified=False)
