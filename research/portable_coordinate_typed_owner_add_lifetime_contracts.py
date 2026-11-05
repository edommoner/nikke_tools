"""Logical owner generations never follow an ADD's label across re-entry."""
import struct

def verify(row,native):
    from portable_coordinate_typed_owner_add_lifetime_cases import prepare
    from portable_coordinate_typed_weapon_contracts import verify as weapons
    c=row if 'original_run' in row else prepare(row)[0];result=weapons(c,native);policy=c['owner_add_lifetime'];original=c['original_run']['prepared']['effects']
    assert len(original)==71 and len(c['effects'])==73
    assert all(e==r['effect'] and c['names'][o]==r['owner'] for e,o,r in zip(c['effects'][:71],c['owners'][:71],original,strict=True))
    owner=[5,1,policy['owner_generation']];physical=[policy['kind'],10,1]
    completes=native['battle']['target_counters']['completions'];assert len(completes)==1
    assert completes[0]['actor']==dict(kind=physical[0],identity=10,generation=1)
    queries=native['coordinate_typed_owner_queries'];assert queries and all(q['physical']==physical and q['logical']==owner for q in queries)
    evidence=native['owner_add_lifetime'];states=evidence['owner_queries'];assert states and all(q['owner']==owner and q['alive'] is not policy['dead_before_child'] for q in states)
    if policy['late']:assert completes[0]['time']>=1.25
    transitions=evidence['field_visibility_transitions'];assert transitions
    assert all(q['field_actor']==owner for q in transitions)
    assert any(not q['visible'] for q in transitions)
    assert any(q['visible'] for q in transitions) is not policy['dead_before_child']
    if policy['repeat']!=1:assert any(q['current_actor'][2]>owner[2] and q['current_alive'] and not q['visible'] for q in transitions)
    carriers=[f for f in native['battle']['enemy_fields']['carriers'] if f['name']=='typed-owner-audit-field'];assert carriers and all(f['actor']==owner for f in carriers)
    final=native['battle']['enemy_fields']['queries'][2]
    if policy['repeat']!=1:assert final[3]>owner[2] and final[4]==1,'The new ADD generation must be alive while the old field is hidden'
    else:assert final[4]==0
    amounts=[struct.unpack('<d',struct.pack('<II',*r[10:12]))[0] for r in native['battle']['enemy_fields']['queries']];assert amounts==[0,0,0],amounts
    return dict(result,verified=True,original_definitions=71,declared_audit_effects=2,owner=owner,physical_handle=physical,counter_completions=1,visibility_transitions=transitions,received_damage_pct=amounts,gpu_supported=False)
