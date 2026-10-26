"""Original current fields plus actual typed-counter owner/aim separation."""
def verify(row,native):
    from portable_coordinate_typed_owner_cases import prepare
    from portable_coordinate_typed_weapon_contracts import verify as weapons
    c=row if 'original_run' in row else prepare(row)[0];proof=weapons(c,native)
    original=c['original_run']['prepared']['effects'];assert len(c['effects'])==len(original)+len(c.get('declared_owner_counter',[]))
    assert all(e==r['effect'] and c['names'][o]==r['owner'] for e,o,r in zip(c['effects'][:len(original)],c['owners'][:len(original)],original,strict=True))
    source=next(e for e in c['effects'] if e.get('name')=='…자고 싶다');assert source['target']=='target' and source['trigger']['timing']==['hit_count:4']
    carriers=native['battle']['enemy_fields']['carriers'];fields=[f for f in carriers if f['name']==source['name']]
    label=c['name'].rsplit('/',1)[-1]
    if label=='control':assert not fields,'Original four-shot field must not activate before its threshold'
    else:
        assert fields,'Original current enemy field must really activate'
        expected=[5,0,1] if label in ('adds','counter-owner-with-adds') else [0,0,1]
        assert all(f['actor']==expected for f in fields),(label,fields)
    projected=native['coordinate_typed_owner_queries']
    assert all(q['physical'][0] in (2,3,4) and q['logical']==[0,0,1] for q in projected)
    if label=='counter-owner-with-adds':
        audit=[f for f in carriers if f['name']=='typed-owner-audit-field'];assert audit and all(f['actor']==[0,0,1] for f in audit)
        assert projected and {q['role'] for q in projected}>={'logical-recipient','target-is-add'}
        from calculator.boss_pattern import AIM_ADDS
        assert all(a['target']==AIM_ADDS for f in native['coordinate_aim']['frames'] for a in f['aims'])
        assert native['coordinate_typed_weapon']['attacks'],'Counter must be fed by actual sampled typed impacts'
        completions=native['battle']['target_counters']['completions'];assert len(completions)==1
        complete=completions[0];physical=dict(kind=3,identity=10,generation=1)
        assert complete['actor']==complete['impact']['target']==physical and complete['reason']=='threshold'
        attacks={r['attack_id']:r for r in native['coordinate_typed_weapon']['attacks']};attack=attacks[complete['impact']['attack_id']]
        assert attack['receipts'][0]['handle']==[3,10,1] and attack['damage']==complete['impact']['damage']
        import struct
        received=lambda r:struct.unpack('<d',struct.pack('<II',*r[10:12]))[0]
        queries=native['battle']['enemy_fields']['queries']
        assert received(queries[0])==17 and all(received(q)==0 for q in queries[1:]),'Owner field must affect BODY queries without leaking to ADD'

    return dict(proof,verified=True,original_definitions=len(original),declared_audit_definitions=len(c.get('declared_owner_counter',[])),original_current_fields=len(fields),logical_owner_queries=len(projected),physical_identity_preserved=True,gpu_supported=False,canonical_consumer_verified=False)
