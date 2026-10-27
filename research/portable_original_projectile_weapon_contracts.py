"""Witness original stat recipients and proc lifetime on real physical receipts."""
def verify(case,native):
    from portable_coordinate_typed_weapon_contracts import verify as weapons
    weapons(case,native)
    typed=native['coordinate_typed_weapon'];attacks=typed['attacks'];samples=typed['modifier_samples']
    name=case['name'];pairs=list(zip(attacks,samples,strict=True))
    if name.endswith('/no-projectiles'):
        assert not pairs,'Delayed typed actors must not receive attacks'
        assert native['physical_pellets'],'Original physical battle must still run'
        return native
    assert pairs and any(a['owner']==0 for a,s in pairs),'Original modifier owner must actually fire'
    assert all(a['receipts'][0]['handle'][0]==2 and s['scalar_kind']==2 for a,s in pairs),'Physical projectile identity must remain typed'
    if '/Sakura/' in name:
        assert all(s['modifier']==7.74 for a,s in pairs),'Original Sakura modifier must apply to every ally'
        assert {a['owner'] for a,s in pairs}==set(range(5))
    elif '/Anchor/' in name:
        assert all(s['modifier']==(25.6 if a['owner']==0 else 0.) for a,s in pairs),'Anchor self modifier must not leak to allies'
        assert {a['owner'] for a,s in pairs}==set(range(5))
    elif '/Clay/' in name:
        assert all(s['modifier'] in (0.,45.05) for a,s in pairs)
        if case['duration']<=3:
            assert all(s['modifier']==0. for a,s in pairs),'No early Clay proc'
        else:
            assert {a['owner'] for a,s in pairs if s['modifier']==45.05}==set(range(5)),'Original count/full-burst proc must reach all allies'
            assert any(s['modifier']==0. for a,s in pairs if a['time']<4.)
            if case['duration']==30:
                late=[s for a,s in pairs if a['time']>=20.]
                assert late and all(s['modifier']==0. for s in late),'Original timed proc must expire'
                assert len(attacks)>2048,'Compare the existing complete stream beyond retained raw capacity'
    else:raise AssertionError('Unknown original modifier contract')
    return native
