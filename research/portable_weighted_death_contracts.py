"""Real down state, frozen shares, and independent cover cancellation witnesses."""
from incoming_weighted_allocation import allocate


def verify(case,native):
    assert native['original_input_identity']==dict(definitions=case['contract']['definitions'],original_definitions_sha256=case['contract']['original_definitions_sha256'],original_effects_and_owners_verified=True)
    data=native['weighted_incoming'];snaps=data['snapshots'];receipts=data['cover_receipts'];hits=native['hits']
    caster=case['names'].index('베이');downs=[h for h in hits if h['down']]
    assert len(downs)==1 and downs[0]['hp_after']==0.
    for s in snaps:
        expected=allocate(s['amount'],s['body_mask'],caster,*data['weights'],bool(s['active_mask']&32))
        for key in ('status','active_mask','total','shares'):assert s[key]==expected[key]
        landed=[h for h in hits if h['time']==s['time']]
        assert {h['owner'] for h in landed}=={i for i in range(5) if s['body_mask']&(1<<i)}
        assert all(h['damage']==s['shares'][h['owner']] for h in landed)
    if case['contract']['scenario']=='caster-during-packet':
        assert downs[0]['owner']==caster
        frozen=next(s for s in snaps if s['time']==downs[0]['time'])
        assert frozen['body_mask']==31 and frozen['active_mask']==63
        canceled=next(r for r in receipts if r['snapshot']==frozen['index'])
        assert canceled['delivered'] is False and canceled['applied']==0.
        assert canceled['hp_before']==canceled['hp_after']>0.
        assert not any(e['time']==canceled['time'] and e['event']=='event:cover_hit' and e['owner']=='베이' for e in native['weighted_notifications'])
        later=[s for s in snaps if s['time']>downs[0]['time']]
        assert later and all(s['body_mask']==30 and s['active_mask']==30 for s in later)
    else:
        assert downs[0]['owner']==2 and downs[0]['time']<snaps[0]['time']
        assert snaps and all(s['body_mask']==27 and s['active_mask']==59 for s in snaps)
        assert receipts and all(r['delivered'] for r in receipts)
    return dict(verified=True,original_definitions=case['contract']['definitions'],actual_downs=1,
        snapshots=len(snaps),canceled_cover_landings=sum(not r['delivered'] for r in receipts),
        existing_hp_and_carrier_state=True,in_game_rules_verified=False,gpu_supported=False)
