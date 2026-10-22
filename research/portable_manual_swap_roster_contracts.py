"""Full original profile coverage is native only, not GPU support."""


def verify(case,native):
    witness=native['manual_swap_roster'];expected=case['contract'];calls=witness['calls']
    assert len(witness['ready'])==expected['ready'],(case['name'],'ready count')
    assert len(calls)==expected['dispatches'],(case['name'],'equivalent dispatches')
    assert witness['physical_shots']==expected['shots'],(case['name'],'physical trace count')
    assert all(c['caster']==case['character'] and c['name']=='저격 모드 탄 소비 집계' and c['value']==40 for c in calls),(case['name'],'exact catalogue dispatch')
    if witness['ready']:assert all(c['time']>witness['ready'][0] for c in calls),(case['name'],'mode entry before charge effect')
    assert case['body']['weapon_mode_swap'] is True,(case['name'],'authored flag')
    return dict(verified=True,reference_model_gap=False,ready_true=len(witness['ready']),catalogue_dispatches=len(calls),physical_shots=witness['physical_shots'],gpu_supported=False)
