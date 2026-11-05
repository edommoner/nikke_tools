"""Distinct logical enemies require delivered receipts, never collider counts."""
def verify(case,native):
    c=case['contract'];groups=native['groups'];notices=native['notices'];children=native['children'];landings=native['child_landings']
    channels=native['logical_pellet_channels'];assert channels
    assert all(p['body']==1. and p['parts']==0 for p in channels if p['front_kind']=='logical_add'),'A logical ADD front hit must retain body-hit notification credit'
    assert all(p['body']==0 and p['parts']==1. for p in channels if p['front_kind']=='parts'),'Canonical PART notification credit must remain separate'
    assert groups and all(g['owner']=='벨로타' and g['finished'] for g in groups)
    assert all(len(g['targets'])==len({tuple(h) for h in g['targets']}) and all(h[0] in (0,5) for h in g['targets']) for g in groups)
    qualifying=[g for g in groups if len(g['targets'])>=4]
    assert [(n['identity'],n['targets']) for n in notices]==[(g['identity'],g['targets']) for g in qualifying]
    assert all(n['event']=='multi_hit:4' for n in notices)
    if c['scenario'] in ('three-enemies','one-outside','part-not-enemy'):
        assert all(len(g['targets'])<=3 for g in groups) and not notices and not children and not landings
        assert not native['enemy_group_fields']
    else:
        assert qualifying and children and landings,'Original four-enemy skill must actually fire'
        assert all(len(g['targets'])==4 for g in qualifying)
        assert {r['name'] for r in children}=={'그리디 2'},'No authored witness skill may replace the original child'
        assert native['enemy_group_fields'] and all(f['name']=='그리디' and f['stat']=='def_pct' and f['recipients'] for f in native['enemy_group_fields']),'Original enemy defense field must activate on actual recipients'
        expected={(0,0,1)} if c['scenario']=='retirement' else {tuple(h) for h in qualifying[0]['targets']}
        assert {tuple(h) for f in native['enemy_group_fields'] for h in f['bound_actors']}==expected,'Original defense field must bind exactly the live group generations'
    if c['part']:
        # The group producer records BODY/ADD receipt membership. Canonical
        # PART landing is retained in the complete SimResult, not that stream.
        assert any(r['target']=='real-part' and r['caster']=='벨로타' for r in native['battle']['hits']),'A real PART must land but cannot satisfy enemy threshold'
    if c['scenario']=='retirement':
        assert groups[0]['targets']==[[0,0,1],[5,2,1],[5,1,1],[5,0,1]]
        assert all(r['target'][0]==0 for r in landings),'Original group child cannot hit an already dead ADD'
        assert native['battle']['add_total']==3
    assert native['original_input_identity']['effects_owners_weapons_chars_config_seed_verified'] and native['original_input_identity']['added_effects']==0
    return dict(verified=True,reference_model_gap=True,original_definition_count=native['original_input_identity']['definitions'],
        actual_groups=len(groups),four_enemy_notifications=len(notices),actual_child_landings=len(landings),
        original_full_roster_preserved=True,logical_ADD_geometry_connected=True,part_is_not_an_enemy=True,
        gpu_wire_connected=False,gpu_supported=False,in_game_rules_verified=False,historical_canonical_equivalence=False)
