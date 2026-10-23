"""Literal current-model contracts, explicitly retaining contradictory annotations."""
def verify(case,native):
    expected=case['contract'];calls=native['skill_weapon_calls']
    assert len(calls)==3,(case['name'],calls)
    assert [r['base'] for r in calls]==[expected['base']]*3
    assert [r['declared'] for r in calls]==[expected['declared']]*3
    assert [r['current'] for r in calls]==expected['current']
    assert [r['explosion'] for r in calls]==expected['explosion']
    assert [r['mode_active'] for r in calls]==expected.get('mode_active',[False]*3)
    assert all(r['owner']==0 and r['normal'] and r['coeff']==100 for r in calls)
    assert [r['damage'] for r in calls]==[12000 if expected['base']=='RL' else 6000]*3
    return dict(verified=True,reference_model_gap=expected['reference_model_gap'],calls=3,declared_weapon_is_not_override=True,actor_base=expected['base'],actual_weapons=expected['current'],mode_active=expected.get('mode_active',[False]*3))
