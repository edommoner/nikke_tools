"""Actual counter completion chooses the declared ADD, not caster aim/BODY."""
import struct

def verify(row,native):
    from portable_coordinate_typed_logical_owner_cases import prepare
    from portable_coordinate_typed_weapon_contracts import verify as weapons
    c=row if 'original_run' in row else prepare(row)[0];result=weapons(c,native);policy=c['logical_owner_contract'];original=c['original_run']['prepared']['effects']
    assert len(original)==71 and len(c['effects'])==73
    assert all(e==r['effect'] and c['names'][o]==r['owner'] for e,o,r in zip(c['effects'][:71],c['owners'][:71],original,strict=True))
    completions=native['battle']['target_counters']['completions'];assert len(completions)==1
    complete=completions[0];handle=[policy['kind'],10,1]
    assert complete['actor']==dict(kind=handle[0],identity=10,generation=1)
    attacks=native['coordinate_typed_weapon']['attacks'];hit=next(r for r in attacks if r['attack_id']==complete['impact']['attack_id'])
    assert hit['receipts'][0]['handle']==handle and hit['receipts'][0]['delivered'] and hit['receipts'][0]['broken'] is policy['dead']
    queries=native['coordinate_typed_owner_queries'];assert queries and all(q['physical']==handle and q['logical']==policy['owner'] for q in queries)
    assert {q['role'] for q in queries}=={'target-is-add','logical-recipient'}
    main=[f for f in native['battle']['enemy_fields']['carriers'] if f['name']=='…자고 싶다']
    assert main and all(f['actor']==[5,0,1] for f in main),'Original current field must retain canonical first-ADD routing'
    child=[f for f in native['battle']['enemy_fields']['carriers'] if f['name']=='typed-owner-audit-field']
    assert child and all(f['actor']==policy['owner'] for f in child)
    received=lambda r:struct.unpack('<d',struct.pack('<II',*r[10:12]))[0]
    amounts=[received(r) for r in native['battle']['enemy_fields']['queries']]
    assert amounts==[0,0,17],amounts
    return dict(result,verified=True,original_definitions=71,declared_audit_effects=2,logical_owner=policy['owner'],physical_handle=handle,counter_completions=1,received_damage_pct=amounts,gpu_supported=False)
