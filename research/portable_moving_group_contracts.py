"""Actual distinct-target notifications and original child damage on movers."""
def verify(case,native):
    from portable_moving_group_cases import prepare_case
    from portable_moving_typed_contracts import verify as physical_contract
    if 'original_run' not in case:case=prepare_case(case)[0]
    rule=case['group_contract']
    result=physical_contract(case,native,require_typed_attacks=not rule['outside'])
    groups=[g for g in native['groups'] if g['owner']==rule['owner']]
    notices=[r for r in native['group_notices'] if r['owner']==rule['owner']]
    children=[r for r in native['group_children'] if r['owner']==rule['owner']]
    landings=[r for r in native['group_child_landings'] if r['owner']==rule['owner']]
    assert groups and all(g['finished'] for g in groups)
    for g in groups:
        assert len(g['targets'])==len({tuple(h) for h in g['targets']})
        assert all(h[0] in (0,5) for h in g['targets'])
    qualifying=[g for g in groups if len(g['targets'])>=2]
    assert len(qualifying)==len(notices)
    assert all(r['event']=='multi_hit:2' and r['targets']==g['targets'] for r,g in zip(notices,qualifying))
    if rule['outside']:
        assert not qualifying and not children and not landings
    else:
        assert qualifying and children and landings
        assert {r['name'] for r in children}=={rule['child']}
        assert any(r['target'][0]==5 for r in landings)
    result.update(actual_group_consumer=True,group_count=len(groups),qualifying_groups=len(qualifying),
        original_child_count=len(children),original_child_landings=len(landings),outside_control=rule['outside'])
    return result
