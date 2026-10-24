"""Native target selection must survive observation and per-pellet destruction."""
def verify(case,n):
    c=case['contract'];groups=n['groups'];shots=n['shots'];notices=n['notifications']
    assert case['routing']=='native' and groups and len(groups)==len(shots)
    assert [g['identity'] for g in groups]==[s['identity'] for s in shots]
    assert all(g['owner']==c['profile'] and g['finished'] for g in groups)
    assert all(s['packets']>=c.get('min_packets',1) for s in shots)
    assert all(len(g['targets'])==len({tuple(h) for h in g['targets']}) for g in groups)
    qualifying=[g for g in groups if len(g['targets'])>=c['threshold']]
    assert [(r['key'][1],r['targets']) for r in notices]==[(g['identity'],g['targets']) for g in qualifying]
    assert all(r['event']=='multi_hit:'+str(c['threshold']) for r in notices)
    if c.get('baseline_unchanged'):
        assert n['battle']==n['baseline']['battle'] and n['projectile_shots']==n['baseline']['projectile_shots']
    if c.get('reselection'):
        assert notices and n['children'] and n['child_landings']
        assert groups[0]['targets']==[[5,0,1],[5,1,1],[5,2,1],[0,0,1]]
        assert all(a['dealt']==1. for a in n['adds'])
        assert all(x['target']==[0,0,1] for x in n['child_landings'])
        assert n['add_overkill']>0
    else:
        target=[5,0,1] if c['adds'] else [0,0,1]
        assert all(g['targets']==[target] for g in groups)
        assert not notices and not n['children'] and not n['child_landings']
    frozen={g['identity']:{tuple(h) for h in g['targets']} for g in qualifying}
    assert all(tuple(x['target']) in frozen[x['group_identity']] for x in n['child_landings'])
    return dict(verified=True,reference_model_gap=True,native_router_unchanged=True,
                baseline_battle_verified=bool(c.get('baseline_unchanged')),
                actual_groups=len(groups),threshold_notifications=len(notices),
                actual_child_landings=len(n['child_landings']),
                per_pellet_reselection_verified=bool(c.get('reselection')),
                full_character_verified=False,gpu_supported=False,in_game_rules_verified=False)
