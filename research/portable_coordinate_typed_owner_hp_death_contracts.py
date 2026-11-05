"""Distinguish HP kills from graph exits and preserve exact owner generation."""
import struct

def verify(row,native):
    from portable_coordinate_typed_owner_hp_death_cases import prepare
    from portable_coordinate_typed_weapon_contracts import verify as weapons
    c=row if 'original_run' in row else prepare(row)[0];result=weapons(c,native);policy=c['owner_hp_death']
    original=c['original_run']['prepared']['effects'];assert len(original)==71 and len(c['effects'])==73
    assert all(e==r['effect'] and c['names'][o]==r['owner'] for e,o,r in zip(c['effects'][:71],c['owners'][:71],original,strict=True))
    node=next(p for p in c['patterns'] if p['id']=='owner-adds');assert node['spec']['hp']==policy['hp'] and not node.get('until') and not node.get('repeat')
    deaths=[]
    for h in native['owner_hp_death']['hits']:
        if h['label']!='__enemy__:owner-adds#2':continue
        assert len(h['before'])==len(h['after'])==1
        a,b=h['before'][0],h['after'][0]
        if a['alive'] and not b['alive']:
            assert h['accepted'] and h['damage']>0 and not a['hit_hp'] and a['hp']==policy['hp']
            assert a['dealt']<a['hp'] and b['dealt']==b['hp']
            assert a['graph_active'] and b['graph_active'] and a['generation']==b['generation']==1
            deaths.append(h)
    assert len(deaths)==1,'Exactly one actual HP kill of the declared ADD owner is required'
    killed=deaths[0]['time'];completes=native['battle']['target_counters']['completions'];assert len(completes)==1
    assert completes[0]['actor']==dict(kind=3,identity=10,generation=1)
    if policy['late']:assert killed<completes[0]['time'] and completes[0]['time']>=1.25
    elif policy['visible_before_death']:assert completes[0]['time']<killed
    else:assert completes[0]['time']==killed
    witness=native['owner_add_lifetime'];queries=witness['owner_queries'];assert queries and all(q['owner']==policy['owner'] and q['alive'] is not policy['late'] for q in queries)
    transitions=witness['field_visibility_transitions'];assert transitions and any(not q['visible'] and not q['current_alive'] for q in transitions)
    assert all(q['field_actor']==q['current_actor']==policy['owner'] for q in transitions)
    assert any(q['visible'] for q in transitions)==policy['visible_before_death']
    fields=native['battle']['enemy_fields'];carriers=[f for f in fields['carriers'] if f['name']=='typed-owner-audit-field'];assert len(carriers)==1 and carriers[0]['actor']==policy['owner']
    final=fields['queries'][2];assert final[1:5]==[5,1,1,0] and struct.unpack('<d',struct.pack('<II',*final[10:12]))[0]==0
    return dict(result,verified=True,original_definitions=71,declared_audit_effects=2,owner=policy['owner'],hp_death_time=killed,counter_completion_time=completes[0]['time'],graph_active_at_hp_death=True,gpu_supported=False)
