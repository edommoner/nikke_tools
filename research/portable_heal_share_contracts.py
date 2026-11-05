"""Literal assertions on actual CPU sharing, before any GPU admission."""


def verify(case,native):
    expected=case['contract'];events=native['heal_share_events']
    plans=[r for r in events if r['kind']=='plan'];originals=[r for r in events if r['kind']=='shared-call'];ends=[r for r in events if r['kind']=='shared-return'];portions=[r for r in events if r['kind']=='portion-call'];notices=[r for r in events if r['kind']=='notify' and r['event']=='event:heal_received']
    assert len(plans)==expected['plans'],(case['name'],'plan count',plans)
    if 'plan_sequence' in expected:assert [r['weights'] for r in plans]==expected['plan_sequence'],(case['name'],'nested plan snapshots',plans)
    else:assert all(r['weights']==expected['weights'] for r in plans),(case['name'],'actual link weights',plans)
    assert len(originals)==len(ends)==len(notices)==expected['notices'],(case['name'],'non-recursive original healing/notifications')
    if 'lifesteal_damage' in expected:
        assert [e['damage'] for e in events if e['kind']=='lifesteal-call']==expected['lifesteal_damage'],(case['name'],'landed lifesteal packets')
    if 'heal_sources' in expected:
        assert [e['heal_source'] for e in notices]==expected['heal_sources'],(case['name'],'original lifesteal source')
    count=sum(len(r['weights']) for r in plans) if plans else expected['notices']
    assert len(portions)==count,(case['name'],'portion count')
    assert [a['hp'] for a in native['allies']]==expected['hp'],(case['name'],'literal HP',[a['hp'] for a in native['allies']])
    assert [a['hp_pct'] for a in native['allies']]==expected.get('hp_pct',[v/100 for v in expected['hp']]),(case['name'],'synchronous HP percent')
    if 'storage' in expected:assert len(native['healing_storage'])==1 and native['healing_storage'][0]['current']==expected['storage'],(case['name'],'full recipient excess storage')
    if 'portion_edges' in expected:
        # Compare the complete per-portion delivery order, not a count of the
        # witness listener's activations. Notifications follow body_heal return
        # and precede the next portion or original shared-return.
        actual=[];current=None
        for event in events:
            if event['kind']=='portion-return':
                current=(event['owner'],[]);actual.append(current)
            elif event['kind'] in ('portion-call','shared-return'):current=None
            elif event['kind']=='notify' and event['event']=='event:adjacent_hp_max':
                assert current is not None,(case['name'],'HP edge outside portion sync')
                assert event['time']==0,(case['name'],'literal HP edge time')
                current[1].append(event['owner'])
        assert actual==expected['portion_edges'],(case['name'],'synchronous HP edge recipients/order',actual)
    if 'notice_order' in expected:
        assert [r['owner'] for r in notices]==expected['notice_order'],(case['name'],'nested notification order')
        assert [r['amount'] for r in originals]==expected['original_amounts'],(case['name'],'literal original amounts')
    if 'portion_sequence' in expected:
        assert [(r['owner'],r['amount']) for r in portions]==expected['portion_sequence'],(case['name'],'literal portion delivery/amounts')
    if 'resumes_after' in expected:
        def position(wanted):
            matches=[i for i,r in enumerate(events) if all(r.get(k)==v for k,v in wanted.items())]
            assert len(matches)==1,(case['name'],'unique nested boundary',wanted)
            return matches[0]
        assert position(expected['resumes_after'])<position(expected['resumes_at']),(case['name'],'outer plan resumes only after nested heal')
    return dict(verified=True,plans=len(plans),original_heals=len(originals),portions=len(portions),original_notifications=len(notices))
