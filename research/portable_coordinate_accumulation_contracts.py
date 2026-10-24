"""Current native consumer exclusion; no unverified claim about game rules."""
def verify(case,native):
    expected=case['expected_accumulation'];data=native['damage_accumulation']
    collected=[e['amount'] for e in data['events'] if e['kind']=='collect']
    assert collected==([2000] if expected else [])
    assert len(data['final']['pools'])==1
    assert data['final']['pools'][0]['current']==expected
    targets=[p for row in native['physical_pellets'] for p in row['packets'] if p['target']]
    assert targets and all(p['damage']>0 for p in targets)
    return dict(verified=True,reference_model_gap=False,
                classification='native_reference_exclusion',
                target_packet_damage=sum(p['damage'] for p in targets),
                accumulated=expected,extra_gpu_accumulation_required_for_parity=False,
                game_rule_verified=False,gpu_supported=False)
