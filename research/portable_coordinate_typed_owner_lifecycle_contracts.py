"""Complete original field/packet state, with living/dead/generation witnesses."""
import struct

def verify(row,native):
    from portable_coordinate_typed_owner_lifecycle_cases import prepare
    from portable_coordinate_typed_weapon_contracts import verify as weapons
    c=row if 'original_run' in row else prepare(row)[0];result=weapons(c,native);policy=c['owner_lifecycle'];original=c['original_run']['prepared']['effects']
    assert len(original)==71 and len(c['effects'])==71+len(c['declared_owner_counter'])
    assert all(e==r['effect'] and c['names'][o]==r['owner'] for e,o,r in zip(c['effects'][:71],c['owners'][:71],original,strict=True))
    fields=native['battle']['enemy_fields'];main=[f for f in fields['carriers'] if f['name']=='…자고 싶다'];assert main and all(f['actor']==([0,0,1] if policy['manual'] else [5,0,1]) for f in main)
    attacks=native['coordinate_typed_weapon']['attacks'];assert attacks
    assert all(r['receipts'][0]['handle'][0]==policy['kind'] for r in attacks)
    completions=native['battle']['target_counters']['completions'];child=[f for f in fields['carriers'] if f['name']=='typed-owner-audit-field'];queries=native['coordinate_typed_owner_queries'];lives=native['owner_query_lifetimes']
    if policy['manual'] or policy['stale_filter']:
        assert not completions and not child and not queries and not lives
        if policy['stale_filter']:
            assert native['battle']['target_counters']['epoch']>0,'The stale marker must really be armed'
            assert c['declared_owner_counter'][0]['trigger']['timing']==['every:1.25s']
            assert any(r['time']>=1.25 and r['receipts'][0]['handle'][2]>1 for r in attacks)
            assert all(r['time']<.5 for r in attacks if r['receipts'][0]['handle'][2]==1)
    else:
        assert len(completions)==1 and child and all(f['actor']==[0,0,1] for f in child)
        complete=completions[0];handle=[policy['kind'],10,policy['generation']]
        assert complete['actor']==complete['impact']['target']==dict(kind=handle[0],identity=10,generation=handle[2]) and complete['reason']=='threshold'
        match=next(r for r in attacks if r['attack_id']==complete['impact']['attack_id']);receipt=match['receipts'][0]
        assert receipt['handle']==handle and match['damage']==complete['impact']['damage'] and receipt['delivered']
        assert bool(receipt['broken']) is policy['dead_query']
        assert queries and all(q['physical']==handle and q['logical']==[0,0,1] for q in queries)
        assert {q['role'] for q in queries}=={'target-is-add','logical-recipient'}
        assert len(lives)==len(queries) and all(q['physical']==handle and q['alive'] is not policy['dead_query'] for q in lives)
        received=lambda r:struct.unpack('<d',struct.pack('<II',*r[10:12]))[0]
        assert received(fields['queries'][0])==17 and all(received(q)==0 for q in fields['queries'][1:])
        if policy['generation']==2:
            assert complete['time']>=.5 and {r['receipts'][0]['handle'][2] for r in attacks}>={1,2}
    return dict(result,verified=True,original_definitions=71,declared_audit_effects=len(c['declared_owner_counter']),owner_query_count=len(queries),owner_query_dead=policy['dead_query'],physical_kind=policy['kind'],counter_generation=policy['generation'],counter_completed=len(completions),stale_counter_suppressed=policy['stale_filter'],gpu_supported=False)
