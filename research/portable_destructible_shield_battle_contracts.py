"""Literal V1 HP-shield policy. No canonical/game or GPU certification."""
EXPECTED={
    'shield-factor-keeps-physical-body':(3872,[1451.,1451.],[7098.]),
    'projectile-factor-does-not-affect-shield':(3872,[968.,968.],[8064.]),
    'break-without-overflow':(4840,[1451.],[0.]),
    'unowned-shield-does-not-intercept':(5808,[],[10000.]),
    'other-owner-does-not-intercept':(5808,[],[10000.]),
    'stale-owner-generation-does-not-intercept':(5808,[],[10000.]),
    'two-shields-in-binding-order':(3872,[1451.,1451.],[0.,3549.]),
    'expired-world-falls-back-to-body':(4840,[1451.],[8549.]),
    'named-coefficient-is-preserved':(3872,[2177.,2177.],[5646.]),
    'expiry-before-second-skill':(3872,[1451.,968.],[7581.]),
    'ordinary-and-target-factor-add':(5416,[1838.,1838.],[6324.]),
    'projectiles-are-not-shields':(5808,[],[10000.]),
    'named-completion-child-reselects-shield':(0,[1451.,726.],[7823.]),
    'death-counter-child-falls-back-to-body':(5324,[1451.],[0.]),
    'next-generation-is-selected-after-respawn':(3872,[1451.,1451.,1451.],[0.]),
}

def verify(case,native):
    name=case['name'].split('/')[-1];body,amounts,remaining=EXPECTED[name]
    assert native['battle']['damage'][0]==body,(name,native['battle']['damage'][0],body)
    assert [r['damage'] for r in native['attacks']]==amounts,(name,native['attacks'])
    assert native['remaining']==remaining,(name,native['remaining'],remaining)
    assert native['finished'] and all(r['completed'] for r in native['attacks'])
    assert all(len(r['receipts'])==1 and r['receipts'][0]['handle'][0]==3 and r['receipts'][0]['delivered'] for r in native['attacks'])
    if name=='two-shields-in-binding-order':assert [r['receipts'][0]['slot'] for r in native['attacks']]==[0,1]
    if name in ('break-without-overflow','death-counter-child-falls-back-to-body'):assert native['attacks'][0]['receipts'][0]['took']==500.
    if name=='next-generation-is-selected-after-respawn':assert [r['receipts'][0]['handle'][2] for r in native['attacks']]==[1,2,3]
    if name=='named-coefficient-is-preserved':assert [r['coefficient'] for r in native['attacks']]==[150.,150.]
    return dict(verified=True,reference_model_gap=True,declared_model=True,canonical_consumer_verified=False,actual_battle_scheduler=True,owner_generation_matched=True,no_overflow=True,physical_weapon_interception=False,hit_shield_interception=False,gpu_connected=False,in_game_rules_verified=False)
