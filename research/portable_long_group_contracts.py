"""Complete actual groups beyond64 and native full-battle parity."""
def verify(case,n):
    c=case['contract'];groups=n['groups'];shots=n['shots'];notices=n['notifications']
    assert len(groups)>64 and len(groups)==len(shots)
    assert all(g['finished'] and g['owner']==c['profile'] for g in groups)
    assert [g['identity'] for g in groups]==list(range(1,len(groups)+1))
    assert all(len(g['targets'])==len({tuple(t) for t in g['targets']}) for g in groups)
    qualifying=[g for g in groups if len(g['targets'])>=c['threshold']]
    assert [(x['key'][1],x['targets']) for x in notices]==[(g['identity'],g['targets']) for g in qualifying]
    if case['routing']=='all-logical-enemies':
        assert all(len(g['targets'])==1+c['adds'] for g in groups)
        assert qualifying and any(x['key'][1]>64 for x in notices)
        frozen={g['identity']:{tuple(t) for t in g['targets']} for g in groups}
        assert all(tuple(x['target']) in frozen[x['group_identity']] for x in n['child_landings'])
    else:
        assert all(g['targets']==[[5,0,1]] for g in groups)
        assert not notices and not n['children']
    if c.get('baseline_unchanged'):
        assert n['battle']==n['baseline']['battle'] and n['projectile_shots']==n['baseline']['projectile_shots']
    return dict(verified=True,reference_model_gap=True,actual_groups=len(groups),groups_after64=len(groups)-64,threshold_notifications=len(notices),full_group_history_required=True,baseline_battle_verified=bool(c.get('baseline_unchanged')),gpu_supported=False,full_character_verified=False)
