"""Actual shield packets must expose original recipients, triggers and expiry."""
def verify(case,native):
    from portable_coordinate_typed_weapon_contracts import verify as weapons
    weapons(case,native)
    typed=native['coordinate_typed_weapon'];pairs=list(zip(typed['attacks'],typed['modifier_samples'],strict=True))
    assert pairs and {a['owner'] for a,s in pairs}==set(range(5)),'All original weapons must fire'
    assert all(a['receipts'][0]['handle'][0]==3 and s['scalar_kind']==3 for a,s in pairs),'Shield identity must not become BODY or projectile'
    name=case['name']
    if '/Rei/' in name or '/Asuka/' in name:
        value=700.5 if '/Rei/' in name else 601.01
        assert all(s['modifier']==(value if a['owner']==0 else 0.) for a,s in pairs),'Permanent self modifier must not leak to other owners'
        if '/Rei/30s' in name:assert len(pairs)>2048,'Whole-stream comparison must exceed retained raw capacity'
    elif '/Mari/' in name:
        assert all(s['modifier'] in (0.,100.09) for a,s in pairs)
        assert {a['owner'] for a,s in pairs if s['modifier']==100.09}==set(range(5)),'Original full-charge proc must reach every ally'
        assert all(s['modifier']==0. for a,s in pairs if a['time']<.9),'No proc before the original first full charge'
    elif '/Misato/' in name:
        assert all(s['modifier'] in (0.,150.) for a,s in pairs)
        assert all(s['modifier']==0. for a,s in pairs if a['time']<2.),'No passive modifier before the original attack-count state'
        assert any(a['owner']==0 and s['modifier']==150. for a,s in pairs),'Actual firing must activate the original passive state'
        if case['duration']>3:assert {a['owner'] for a,s in pairs if s['modifier']==150.}==set(range(5)),'Original passive state condition must reach every ally'
    else:raise AssertionError('Unknown original shield modifier contract')
    if case.get('declared_manual_sequences'):
        identity=native['original_input_identity']
        assert identity['declared_manual_sequences_applied_after_identity_check'] and identity['original_controls_preserved'] is False
        at,length=(2.,6.) if '/Mari/' in name else (7.,8.)
        assert not any(a['owner']==0 and at<=a['time']<at+length for a,s in pairs),'Original caster must really stop firing while covered'
        start,end=(5.,7.) if '/Mari/' in name else (11.,14.)
        expired=[s for a,s in pairs if start<=a['time']<end]
        assert expired and all(s['modifier']==0. for s in expired),'Original effect/state must expire during cover'
        resumed=9. if '/Mari/' in name else 19.
        assert any(s['modifier']>0 for a,s in pairs if a['time']>=resumed),'Original firing must reactivate the modifier after cover'
    return native
