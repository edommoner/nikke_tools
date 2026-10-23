"""Original global removal is triggered at30s and never queries the target selector."""
def verify(case,native):
    c=case['contract'];o=native['named_enemy_removal'];calls=o['removals']
    assert len(calls)==c['dispatches'] and sum(len(v['events']) for v in calls)==c['ended']
    assert o['selection']==dict(rankings=[],recipients=[])
    for row in calls:
        assert row['owner']==0 and len(row['before'])==1 and row['after']==[]
        assert row['before'][0]==dict(owner=0,members=['__enemy__'])
        assert row['events']==[dict(event='event:state_end:안티 AT 필드',time=row['time'],owner=0,remaining=[])]
    return dict(verified=True,reference_model_gap=False,dispatches=len(calls),state_end_notifications=c['ended'],original_definitions=True,global_ignores_target=True,shots=len(native['projectile_shots']))
