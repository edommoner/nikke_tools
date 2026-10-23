"""Literal scalar amounts, rate ownership, archive selection and full-notice order."""
TAKES={'dealt-default':[900],'received-default':[4500],'last-owner-dealt':[900],
'dealt-ignores-other-casters':[0],'received-counts-other-casters':[3600],'base50':[450],
'base50-named25':[675],'absent-base':[900],'explicit-zero-base':[0],
'absent-base-named25':[1125],'zero-base-named25':[225],'empty-values-is-zero':[0],
'wrong-named-rate':[900],'wrong-caster-rate':[900],'own-rate-wrong-recipient':[450],
 'two-baseline-rates':[675],'negative-rate':[-450],'cap-clamp':[500],'zero-cap':[0],
'negative-cap':[0],'epsilon-inside':[900],'epsilon-outside':[900],'initial-ATK':[1900],
'later-ATK-keeps-cap':[1000],'empty-expiry':[0],'archived-consume-once':[900,0],
'active-consume-once':[900,0],'missing-name':[0],'cross-owner-active':[900],
'cross-owner-archive':[900],'refresh-clears-archive':[0],'refresh-collects-new-lifetime':[900],'named-removal-retains-archive':[900],
'split-only-and-int-truncation':[900],'no-second-attack-modifier':[900],
'lifesteal-before-rate':[369],'scatter-two-muzzles':[1800],'add-share-excluded':[0],'explicit-boss-share':[300],
'all-pools-full-before-notices':[500,500],'duplicate-name-first-active':[900,0],
'duplicate-name-last-archive':[4500],'pool-target-does-not-filter-damage':[900],
'stacked-rate':[1800],'down-keeps-name-archive':[900],'release-feeds-another-pool':[900,9900],
'rate-expired-before-hit':[900],'last-owner-cap-snapshot':[2000],'dealt-group-before-received':[500,500],'ordered-baseline-cancellation':[9],'separate-baseline-and-named-groups':[9],'duplicate-name-active-reverse-stat-order':[4500,0]}
def verify(case,native):
    kind=case['contract']['kind'];data=native['damage_accumulation'];events=data['events'];takes=[e for e in events if e['kind']=='take'];notices=[e for e in events if e['kind']=='full-notice'];emissions=[e for e in events if e['kind']=='emission']
    assert [e['value'] for e in takes]==TAKES[kind],(kind,[e['value'] for e in takes],TAKES[kind])
    assert all(e['split'] and not e['critical'] and type(e['amount']) is int for e in emissions)
    if kind=='named-removal-retains-archive':assert not takes[0]['before']['pools'] and takes[0]['before']['archive']['pool']==900
    if kind=='cross-owner-active':assert takes[0]['requester']==1 and takes[0]['before']['pools'][0]['owner']==0 and takes[0]['after']['pools'][0]['done']
    if kind=='cross-owner-archive':assert takes[0]['requester']==1 and not takes[0]['before']['pools']
    expected_rates={'base50':50,'base50-named25':75,'absent-base':100,'explicit-zero-base':0,'absent-base-named25':125,'zero-base-named25':25,'empty-values-is-zero':0,'wrong-named-rate':100,'wrong-caster-rate':100,'own-rate-wrong-recipient':50,'two-baseline-rates':75,'negative-rate':-50,'lifesteal-before-rate':41,'stacked-rate':200,'ordered-baseline-cancellation':1,'separate-baseline-and-named-groups':1}
    if kind in expected_rates:assert [e['value'] for e in events if e['kind']=='rate']==[expected_rates[kind]],(kind,[e['value'] for e in events if e['kind']=='rate'])
    if kind=='negative-cap':assert any(p['base']==-1000 for e in events if 'after' in e for p in e['after']['pools'])
    if kind=='epsilon-inside':assert len(notices)==1 and any(p['current']<p['base'] and p['done'] for p in notices[0]['before']['pools'])
    if kind=='epsilon-outside':assert not notices
    if kind=='initial-ATK':assert any(p['base']==2000 for e in events if 'after' in e for p in e['after']['pools'])
    if kind=='later-ATK-keeps-cap':assert all(p['base']==1000 for e in events if 'after' in e for p in e['after']['pools'])
    if kind in ('refresh-clears-archive','refresh-collects-new-lifetime'):assert any(e['kind']=='snapshot' and e['before']['archive'].get('pool',0)>0 and e['after']['archive']['pool']==0 for e in events)
    if kind=='refresh-clears-archive':assert native['shots'][0]==1 and any(e['owner']==0 and e['kind']=='start' for e in native['reload_events'])
    if kind=='split-only-and-int-truncation':assert [e['amount'] for e in emissions]==[1126]
    if kind=='no-second-attack-modifier':assert [e['amount'] for e in emissions]==[900]
    if kind=='all-pools-full-before-notices':
        assert [e['name'] for e in notices]==['first','second']
        assert len(notices[0]['before']['pools'])==2 and all(p['done'] for p in notices[0]['before']['pools'])
    if kind=='dealt-group-before-received':
        assert [e['name'] for e in notices]==['dealt-second','received-first']
        assert [p['name'] for p in notices[0]['before']['pools']]==['received-first','dealt-second'] and all(p['done'] for p in notices[0]['before']['pools'])
    if kind=='duplicate-name-active-reverse-stat-order':assert takes[0]['requester']==2 and takes[0]['before']['pools'][0]['stat']=='dmg_accum_received_atk_pct' and takes[0]['after']['pools'][0]['done']
    if kind=='duplicate-name-first-active':assert takes[0]['requester']==2 and takes[1]['requester']==3 and takes[0]['before']['pools'][0]['owner']==0
    if kind=='scatter-two-muzzles':assert [e['amount'] for e in events if e['kind']=='collect' and e['owner']==0 and e['before']['pools']]==[300]*6
    if kind=='add-share-excluded':assert sum(native['actor_add_damage'])>0 and not any(e['kind']=='collect' and e['before']['pools'] for e in events)
    if kind=='explicit-boss-share':assert [e['amount'] for e in events if e['kind']=='collect' and e['owner']==0 and e['before']['pools']]==[300]
    if kind=='down-keeps-name-archive':assert native['allies'][0]['down'] and takes[0]['before']['archive']['pool']==900
    return dict(verified=True,reference_model_gap=False,declared_model=True,in_game_rules_verified=False,takes=TAKES[kind],full_notices=len(notices),emitted_amounts=[e['amount'] for e in emissions],collection_calls=sum(e['kind']=='collect' for e in events))
