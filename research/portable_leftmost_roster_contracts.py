"""Literal native target choices; original definitions remain intact."""
def verify(case,native):
    selections=native['leftmost_selections'];picked=case['contract']['picked']
    assert selections,(case['name'],'battle-start selection missing')
    assert all(r['owner']==0 and r['target']=='allies_code_weapon_leftmost:전격:AR:1' and r['picked']==picked for r in selections),(case['name'],selections)
    return dict(verified=True,reference_model_gap=False,selections=len(selections),picked=picked,shots=len(native['projectile_shots']))
