"""Ownership, per-caster thresholds, full groups and original battle parity."""
def verify(case,n):
    c=case['contract'];owners=c['mixed_owners'];groups=n['groups'];shots=n['shots'];notices=n['notifications']
    assert groups and len(groups)==len(shots)
    assert {g['owner'] for g in groups}==set(owners)
    assert [(g['identity'],g['owner']) for g in groups]==[(s['identity'],s['owner']) for s in shots]
    assert [g['identity'] for g in groups]==list(range(1,len(groups)+1))
    assert all(g['finished'] and s['packets']>0 and g['time']==s['time'] for g,s in zip(groups,shots,strict=True))
    assert all(len(g['targets'])==len({tuple(t) for t in g['targets']}) for g in groups)
    expected=[g for g in groups if len(g['targets'])>=owners[g['owner']]]
    assert [(v['owner'],v['event'],v['key'],v['targets'],v['time']) for v in notices]==[(g['owner'],'multi_hit:'+str(owners[g['owner']]),[g['owner'],g['identity'],g['epoch']],g['targets'],g['time']) for g in expected]
    frozen={g['identity']:g for g in groups}
    assert all(x['owner']==frozen[x['group_identity']]['owner'] and tuple(x['target']) in {tuple(t) for t in frozen[x['group_identity']]['targets']} for x in n['child_landings'])
    if case['routing']=='native':
        assert all(g['targets']==[[5,0,1]] for g in groups)
        assert not notices and not n['children'] and not n['child_landings']
        assert n['battle']==n['baseline']['battle'] and n['projectile_shots']==n['baseline']['projectile_shots']
    else:
        assert all(len(g['targets'])==1+c['adds'] for g in groups)
        assert any(v['owner']=='니힐리스타' for v in notices)
        assert any(v['owner']=='벨로타' for v in notices)==(c['adds']>=3)
    if c['duration']==180:assert len(groups)>64 and len({g['owner'] for g in groups[64:]})==2
    return dict(verified=True,reference_model_gap=True,owners=sorted(owners),actual_groups=len(groups),threshold_notifications=len(notices),actual_child_landings=len(n['child_landings']),baseline_battle_verified=case['routing']=='native',full_group_history_required=True,gpu_supported=False,full_character_verified=False)
