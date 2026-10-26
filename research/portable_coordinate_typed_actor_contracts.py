"""Real original skill notifications and ordinary BODY/ADD selection witnesses."""
def verify(row,native):
    from portable_coordinate_typed_weapon_cases import prepare
    from portable_coordinate_typed_weapon_contracts import verify as weapons
    case=row if 'original_run' in row else prepare(row)[0]
    result=weapons(case,native);source=next(i for i,e in enumerate(case['effects']) if e.get('target')=='enemies_nearest_in_range')
    effect=case['effects'][source];assert effect['trigger']['timing']==['hit_count:100']
    assert effect['name']=='선두 제압 2'
    # Source/owner/order are additionally checked by the existing original
    # registration guard; this observer does not insert a probe definition.
    queries=[q for q in native['coordinate_typed_actor_queries'] if q['skill']==effect['name']]
    packets=[p for p in native['landed_packets'] if p['skill_name']==effect['name']]
    events=[r for r in native['skill_trace'] if r['row']==source]
    label=case['name'].rsplit('/',1)[-1]
    if label=='control':assert not queries and not packets and not events,'The original100-shot trigger must not fire early'
    else:
        assert packets and events,'Original current-target skill must really execute'
        wanted='__enemy__:logical-adds#1' if label=='adds' else ''
        assert all(p['target']==wanted for p in packets),(label,packets)
        assert len(events)==len(packets)
        assert all(e['landed']==p['time'] and e['share']==p['damage'] for e,p in zip(events,packets,strict=True))
        if label in ('adds','manual-typed-with-adds'):
            assert queries,'Real ADD routing must consult the canonical enemy selector'
            logical=wanted or '__enemy__'
            assert all(q['logical']==logical for q in queries),(label,queries)
        if label=='manual-typed-with-adds':assert all(q['aim']=='typed-back' for q in queries)
        if label=='body':assert all(a['target']=='typed-front' for f in native['coordinate_aim']['frames'] for a in f['aims'])
    return dict(result,verified=True,original_current_skill_events=len(events),original_source_index=source,original_definitions=len(case['effects']),logical_enemy_queries=len(queries),gpu_supported=False,canonical_consumer_verified=False)
