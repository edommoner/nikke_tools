"""Assertions on actual pinned execution, reusable before and after the GPU port."""

def verify(case,native):
    name=case['name'];events=native['revival_events']
    downs=[e for e in events if e['kind']=='after-down'];ups=[e for e in events if e['kind']=='after-revive'];actions=[e for e in events if e['kind']=='action-revive']
    expected_ups=0 if name in ('revive-down-control','revive-alive-noop','revive-class-random-empty') else 1
    assert len(ups)==len(actions)==expected_ups,(name,'revive count')
    assert len(downs)==(0 if name=='revive-alive-noop' else 5 if name=='revive-whole-squad' else 2 if name in ('revive-once-only','revive-caster-down') else 1),(name,'down count')
    for e in downs:
        i=e['owner'];s=e['state'];assert i in s['down'] and s['hp'][i]==s['hp_pct'][i]==0,(name,'down HP')
    for e in ups:
        i=e['owner'];s=e['state'];assert i==0 and i not in s['down'] and s['hp_pct'][i]==50,(name,'revived identity/HP')
        assert s['hp'][i]==(6250 if name=='revive-passive-not-periodic' else 5000),(name,'passive max HP')
    for a in actions:
        assert all(a[k]==-1 for k in ('reload_until','post_reload','charge_full','hold_release','cover_until')),(name,'action reset')
        assert not a['cover_until_reload'] and not a['charging'] and a['charge_phase']=='ready',(name,'charge/cover reset')
        assert a['ammo']==(10 if name=='revive-restored-max-ammo' else 3) and a['next_fire']==a['time'],(name,'full ammo/immediate resume')
    if ups:
        up=ups[0];i=events.index(up);action=next(j for j,e in enumerate(events) if e['kind']=='action-revive')
        down_action=next(j for j,e in enumerate(events) if e['kind']=='action-down' and e['owner']==0)
        assert down_action<i<action,(name,'down cleanup must precede synchronous revive')
        active=up['state']['active'];present=lambda label:[a for a in active if a['name']==label and 0 in (a['recipients'] or [])]
        assert len(present('own-permanent'))==1,(name,'own permanent restored')
        shared=present('shared-permanent');assert len(shared)==1 and shared[0]['stack']==1 and shared[0]['recipients']==([1,3,4,0] if name=='revive-caster-down' else [1,2,3,4,0]),(name,'shared identity/order/stack')
        before=next(e for e in events if e['kind']=='before-down' and e['owner']==0)['state']['active']
        assert shared[0]['identity']==next(a['identity'] for a in before if a['name']=='shared-permanent'),(name,'shared carrier reused')
        if name in ('revive-marker-self','revive-marker-shared','revive-preserved-marker'):
            marker=present('persona-marker');assert len(marker)==1 and marker[0]['stack']==1
            assert marker[0]['recipients']==([1,2,3,4,0] if name=='revive-marker-shared' else [0])
        if name=='revive-preserved':
            marker=present('preserved')[0];after_down=next(e for e in downs if e['owner']==0)['state']['active']
            assert marker['identity']==next(a['identity'] for a in after_down if a['name']=='preserved' and 0 in a['recipients'])
        for label,case_name in [('periodic-permanent','revive-passive-not-periodic'),('dead-caster-passive','revive-caster-down'),('finite-passive','revive-finite-passive'),('bullet-passive','revive-bullet-passive')]:
            if name==case_name:assert not present(label),(name,label+' must not be restored')
    if name=='revive-no-hp-threshold':assert not any(e['kind']=='notify' and e['event'].startswith('hp_below:') for e in events)
    if name in ('revive-synchronous','revive-class-random'):
        assert [e['owner'] for e in events if e['kind']=='notify' and e['event']=='event:ally_down']==[1,2,3,4]
    if name in ('revive-shared-no-renotify','revive-own-renotify'):
        children=[a for a in native['named_state']['allied_carriers'] if a['name']=='named-child']
        assert children and any(0 in (a['recipients'] or []) for a in children)==(name=='revive-own-renotify'),(name,'existing versus recreated parent notification')
    if name=='revive-self-down-broadcast':
        assert [e['owner'] for e in events if e['kind']=='notify' and e['event']=='event:ally_down']==[0,1,2,3,4]
        assert any(a['name']=='notified-after-self-revive' for a in native['named_state']['allied_carriers'])
    if name=='revive-once-only':assert native['allies'][0]['down'] and native['allies'][0]['hp']==0
    if name=='revive-delayed':assert ups[0]['time']>downs[0]['time']
    if name=='revive-caster-down':assert native['allies'][2]['down'] and not native['allies'][0]['down']
    if name.startswith('revive-class-random'):
        target=next(e for e in events if e['kind']=='target')
        assert target['result']==([] if name.endswith('empty') else [0])
        assert (target['random_before']==target['random_after'])==name.endswith('empty'),(name,'independent global RNG consumption')
    return dict(downs=len(downs),revives=len(ups),actions=len(actions),verified=True)
