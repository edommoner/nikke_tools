"""Original two-enemy damage requires distinct actual BODY/ADD receipts."""
def verify(case,native):
    c=case.get('logical_geometry_contract',case.get('contract'));groups=native['groups']
    full='logical_geometry' in native
    notices=native['group_notices' if full else 'notices'];children=native['group_children' if full else 'children']
    landings=native['group_child_landings' if full else 'child_landings']
    assert native['original_input_identity']['definitions']==c['definitions']
    assert groups and all(g['owner']==c['owner'] and g['finished'] for g in groups)
    assert all(len(g['targets'])==len({tuple(h) for h in g['targets']}) and all(h[0] in (0,5) for h in g['targets']) for g in groups)
    qualifying=[g for g in groups if len(g['targets'])>=c['threshold']]
    assert len(notices)==len(qualifying)
    assert all(n['event']=='multi_hit:2' and n['targets']==g['targets'] for n,g in zip(notices,qualifying))
    if c['outside']:
        assert all(len(g['targets'])<=1 for g in groups) and any(g['targets']==[[0,0,1]] for g in groups)
        assert not notices and not children and not landings
    else:
        assert qualifying and children and landings
        assert all(g['targets']==[[0,0,1],[5,0,1]] for g in qualifying)
        assert {r['name'] for r in children}=={c['child']}
        assert {tuple(r['target']) for r in landings}=={(0,0,1),(5,0,1)}
    if c['part'] and not full:
        assert any(h['caster']==c['owner'] and h['target']=='real-part' for h in native['battle']['hits'])
    return dict(verified=True,reference_model_gap=True,original_roster_preserved=True,
        original_definition_count=c['definitions'],actual_groups=len(groups),threshold_notifications=len(notices),
        actual_child_landings=len(landings),part_is_not_an_enemy=True,gpu_supported=False,
        historical_canonical_equivalence=False,in_game_rules_verified=False)
