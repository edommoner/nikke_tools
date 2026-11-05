"""Full-profile ticks must actually reach the original annotated auto skill."""
def verify(case,native):
    calls=native['skill_weapon_calls'];expected=2 if case['contract']['duration']==3 else 77
    assert len(calls)==expected,(case['name'],len(calls),expected)
    assert all(r['owner']==0 and r['base']==r['declared']==r['current']=='RL' and r['normal'] and r['explosion'] and r['coeff']==40.01 for r in calls)
    return dict(verified=True,reference_model_gap=False,actual_calculator_calls=len(calls),handler_reached=True,declared_weapon_is_not_override=True,shots=len(native['projectile_shots']))
