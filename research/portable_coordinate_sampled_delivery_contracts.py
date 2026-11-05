"""Actual skill-mode exclusion, sampled MT and typed receipt ownership."""
def verify(case,native):
    from portable_coordinate_sampled_vital_contracts import verify as vital
    from portable_coordinate_group_contracts import verify_groups
    answer=vital(case,native);label=case['name'].rsplit('/',1)[1]
    if label.startswith('skill-'):assert any(s['skill_damage'] for s in native['sampled_live_shots'])
    if case.get('sampled_groups'):
        if label=='group-skill-excluded':
            assert native['sampled_live_shots'] and all(s['skill_damage'] for s in native['sampled_live_shots'])
            assert not any(native[k] for k in ('groups','group_shots','group_notices','group_receipts','group_children','group_child_landings'))
        else:
            verify_groups(native)
            groups={(g['owner'],g['identity']):g for g in native['groups']}
            for child in native['group_children']:
                group=groups[child['owner'],child['group_identity']]
                assert child['targets']==group['targets'] and child['time']==group['time']
            for landing in native['group_child_landings']:
                assert landing['target'] in groups[landing['owner'],landing['group_identity']]['targets']
        if label.startswith('group-add-'):assert any(r['target'][0]==5 for r in native['group_receipts'])
        answer.update(groups=len(native['groups']),receipts=len(native['group_receipts']),notifications=len(native['group_notices']),children=len(native['group_children']))
    return answer
