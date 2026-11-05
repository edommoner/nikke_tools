"""Authored selection, partial memberships, snapshot scope and callback order."""
def verify(case,native):
    c=case['contract'];o=native['named_enemy_removal'];selection=o['selection'];calls=o['removals'];assert len(calls)==3
    assert len(selection['rankings'])==c['rank_calls'] and len(selection['recipients'])==c['recipient_calls']
    if c['scope']=='target':
        assert [r['picked'] for r in selection['recipients']]==c['picked']
        for i,r in enumerate(selection['rankings']):
            assert r['target']=='enemies_with_buff:'+c['mark_name'] and r['owner']==0
            assert [v['identity'] for v in r['checks']]==c['pool']
            assert all(v['name']==c['mark_name'] for v in r['checks'])
            marked=c['marked'] if i==0 or not c['removed_marker'] else []
            assert [v['identity'] for v in r['checks'] if v['present']]==marked
            assert r['order']==c['picked'][i] and r['count']==len(c['picked'][i])
    for i,row in enumerate(calls):
        assert row['owner']==0 and abs(row['time']-[0,7/60,13/60][i])<1e-12
        owner=0 if c['removed_marker'] else c['payload_owner'];before=c['initial'] if i==0 else c['remaining'];after=c['remaining']
        assert row['before']==[dict(owner=owner,members=[v]) for v in before],(case['name'],i,'before',row)
        assert row['after']==[dict(owner=owner,members=[v]) for v in after],(case['name'],i,'after',row)
        gone=[v for v in before if v not in after]
        expected=[dict(event='event:state_end:'+c['removed_name'],time=row['time'],owner=owner,remaining=[dict(owner=owner,members=[v]) for v in after]) for _ in gone]
        assert row['events']==expected,(case['name'],i,'events',row)
    assert native['rng']['draws']==0 and native['named_state']['allied_carriers']==[]
    return dict(verified=True,reference_model_gap=False,dispatches=3,rankings=c['rank_calls'],recipient_resolutions=c['recipient_calls'],membership_checks=sum(len(r['checks']) for r in selection['rankings']),global_ignores_target=c['global_ignores_target'],remaining=c['remaining'])
