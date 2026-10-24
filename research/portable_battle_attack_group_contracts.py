"""Nonzero original multi_hit children and immutable logical enemy generations."""
def verify(case,n):
    c=case['contract'];owner=c['profile'];threshold=c['threshold'];groups=n['groups'];shots=n['shots'];notices=n['notifications'];children=n['children'];landings=n['child_landings']
    assert groups and len(groups)==len(shots) and all(g['owner']==owner and g['finished'] for g in groups)
    assert [g['identity'] for g in groups]==[s['identity'] for s in shots]
    assert all(len(g['targets'])==len({tuple(h) for h in g['targets']}) and all(h[0] in (0,5) for h in g['targets']) for g in groups)
    assert all(s['packets']>=c.get('min_packets',1) for s in shots)
    qualifying=[g for g in groups if len(g['targets'])>=threshold]
    assert [(r['key'][1],r['targets']) for r in notices]==[(g['identity'],g['targets']) for g in qualifying]
    assert all(r['event']=='multi_hit:'+str(threshold) for r in notices)
    assert len(children)==len(qualifying)
    assert all(x['damage']>0 and x['targets']==g['targets'] and x['group_identity']==g['identity'] for x,g in zip(children,qualifying,strict=True))
    frozen={child['group_identity']:{tuple(h) for h in child['targets']} for child in children}
    assert all(tuple(r['target']) in frozen.get(r['group_identity'],set()) and r['damage']>=0 for r in landings)
    if c['capacity']==1. or c.get('reopened'):
        assert qualifying and landings and all(r['target']==[0,0,1] for r in landings)
        if c.get('reopened'):assert n['adds'] and all(a['handle'][2]==2 for a in n['adds'])
        else:assert all(not a['alive'] for a in n['adds'])
    else:
        assert all(len(g['targets'])==1+c['adds'] for g in groups)
        if 1+c['adds']>=threshold:
            assert qualifying and landings
            assert all(len([r for r in landings if r['group_identity']==child['group_identity']])==1+c['adds'] for child in children)
            if threshold==4:
                fields=[x for x in n['fields'] if x['name']=='그리디'];assert len(fields)==1+c['adds']
                assert {tuple(h) for x in fields for h in x['handles']}=={tuple(h) for h in groups[-1]['targets']}
        else:assert not qualifying and not children and not landings
    return dict(verified=True,reference_model_gap=True,declared_whole_scene_routing=True,actual_shots=len(shots),actual_groups=len(groups),threshold_notifications=len(notices),positive_children=len(children),actual_child_landings=len(landings),full_character_verified=False,gpu_supported=False,in_game_rules_verified=False)
