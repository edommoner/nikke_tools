"""Original four-stage identity, actual split landings and independent cover."""
from incoming_weighted_allocation import allocate

def verify(case,native):
    c=case['contract'];data=native['weighted_incoming'];snapshots=data['snapshots'];receipts=data['cover_receipts'];hits=native['hits'];names=case['names']
    assert native['original_input_identity']==dict(definitions=c['definitions'],original_definitions_sha256=c['original_definitions_sha256'],original_effects_and_owners_verified=True)
    assert all(m['owner']=='베이' and m['effect']['stat']=='received_dmg_split' for m in c['original_markers'])
    if c['scenario']=='inactive':
        assert not snapshots and not receipts and native['inactive_transparent']
        assert len(hits)==1 and len([e for e in native['weighted_notifications'] if e['event']=='received_hit'])==1
        return dict(verified=True,inactive_complete_battle_transparent=True,gpu_wire_connected=False)
    assert snapshots and all(s['status']==0 and s['caster']=='베이' for s in snapshots)
    assert len([e for e in native['weighted_notifications'] if e['event']=='received_hit'])==len(case['patterns'])-1,'Only literal hit targets receive the original hit notification'
    for s in snapshots:
        expected=allocate(s['amount'],s['body_mask'],names.index(s['caster']),*data['weights'],bool(s['active_mask']&32))
        for key in ('active_mask','total','shares'):assert s[key]==expected[key]
        assert s['body_source_name']==next(m['effect']['name'] for m in c['original_markers'] if m['effect']['target']=='all_allies')
        assert s['body_source_activated_at']<=s['time']
        landed=[h for h in hits if h['time']==s['time']]
        assert {h['owner'] for h in landed}=={i for i in range(5) if s['body_mask']&(1<<i)}
        assert all(h['damage']==s['shares'][h['owner']] for h in landed),'Every actual body share goes through the existing landing executor'
        assert len([e for e in native['weighted_notifications'] if e['event']=='received_hit' and e['time']==s['time'] and e['owner']==s['struck']])==1
    assert len(receipts)==sum(bool(s['active_mask']&32) for s in snapshots)
    for r in receipts:
        s=snapshots[r['snapshot']];assert s['time']==r['time']
        assert r['delivered'] and r['applied']==min(r['hp_before'],s['shares'][5]) and r['hp_after']==r['hp_before']-r['applied']
        assert any(e['event']=='event:cover_hit' and e['time']==r['time'] and e['owner']==s['caster'] for e in native['weighted_notifications'])
    if c['scenario'] in ('break-no-revive-reburst','Biscuit-revive-reburst'):
        broken=[r for r in receipts if r['hp_after']==0.]
        assert broken,'Literal original-world attack must actually destroy Bay cover'
        first=broken[0]['snapshot'];assert any(not s['active_mask']&32 for s in snapshots[first+1:]),'Next packet excludes broken independent cover'
        if c['scenario']=='Biscuit-revive-reburst':
            assert any(r['snapshot']>first and r['hp_before']>0. for r in receipts),'Original Biscuit cover revival must restore later cover participation'
            assert any(b['event']==2 and b['owner']==names.index('비스킷') for b in native['burst_trace'])
        else:
            assert all(not s['active_mask']&32 for s in snapshots[first+1:]),'Ordinary cover healing must not revive destroyed cover'
        assert len({s['body_source_activated_at'] for s in snapshots})>=2,'Original second burst must refresh the same real carrier'
    return dict(verified=True,declared_model=True,original_definitions=c['definitions'],favorite_stage=c['favorite_stage'],snapshots=len(snapshots),independent_cover_landings=len(receipts),body_landings=len(hits),cover_breaks=sum(r['hp_after']==0. for r in receipts),original_burst_epochs=len({s['body_source_activated_at'] for s in snapshots}),gpu_wire_connected=False,gpu_supported=False,in_game_rules_verified=False)
