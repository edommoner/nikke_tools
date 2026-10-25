"""Literal legal split weights and mixed-world witnesses; not admission proof."""
from portable_coordinate_group_contracts import verify_groups
COUNTS=[4,4,4,4,3,4,3,4,4,4,4,4,4,4,4,2,4,4,4]

def verify(case,native):
    from portable_coordinate_mixed_cases import fixtures
    names=[c['name'] for c in fixtures()];label=case['name'].split('mixed-')[-1]
    assert native['reference_kind']=='deterministic-common-cpu'
    assert len(native['groups'])==COUNTS[names.index(case['name'])]
    verify_groups(native)
    targets=[g['targets'] for g in native['groups']]
    if label=='split-add-retirement':expected=[[[5,0,1]]]+[[[0,0,1]]]*3
    elif label=='shield-0':expected=[[],[],[[0,0,1]],[[0,0,1]]]
    else:
        add=any(p['kind']=='summon' for p in case['patterns'])
        expected=[[[5,0,1] if add else [0,0,1]]]*len(targets)
    assert targets==expected,(label,targets,expected)
    actual=[(p['label'],p['damage']) for p in native['landed_packets'] if p['skill_name']=='mixed-split']
    literal={
        'split-all':[('__enemy__',667),('__enemy__:adds#1',667),('__enemy__:adds#2',667)],
        'split-add-retirement':[('__enemy__',667),('__enemy__:adds#2',667),('__enemy__:adds#3',667)],
        'split-ranked':[('__enemy__',1000),('__enemy__:adds#1',1000)],
        'split-random':[('__enemy__',667),('__enemy__:adds#2',667),('__enemy__:adds#4',667)],
        'split-tie-odd':[('__enemy__',2),('__enemy__:adds#1',2)],
        'split-tie-even':[('__enemy__',2),('__enemy__:adds#1',2)],
        'split-round-zero':[('__enemy__',0),('__enemy__:adds#1',0),('__enemy__:adds#2',0)],
        'combined-split-parts':[('__enemy__',667),('__enemy__:adds#1',667),('__enemy__:adds#2',667),('front',3000),('behind',3000)],
    }
    assert actual==literal.get(label,[]),(label,actual)
    if 'boss-attack' in label or label=='combined-split-parts':
        assert [a['received_hits'] for a in native['battle']['allies']]==[3]*5
        assert all(a['received_damage']==900 for a in native['battle']['allies'][1:])
    if label=='combined-split-parts':assert native['battle']['covers'][0]['hp']==700
    assert all(p['damage']>=0 and p['generation']>=1 for p in native['landed_packets'])
    assert all(r['expected'] for r in native['physical_pellets'])
    return dict(verified=True,reference_model_gap=False,reference_kind='deterministic-common-cpu',groups=len(targets),landed_packets=len(native['landed_packets']),split_packets=len(actual),gpu_supported=False)
