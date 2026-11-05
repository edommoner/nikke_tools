"""Literal presence and pre-weapon aim contracts for the pinned native model."""
def verify(case,native):
    rows=native['focus_aim'];assert rows,(case['name'],'aim observations')
    label=case['name'].removeprefix('focus-aim-').removesuffix('-aim-only')
    adds='__enemy__:*';partial=['stop',adds,adds,adds,adds];full=['stop']*5
    first=last=full
    if label in ('absent','name-is-not-stat','unfocused-runtime'):first=last=partial
    elif label=='recipient-self':first=last=['stop','stop',adds,adds,adds]
    elif label=='foreign-recipient':first=last=['stop',adds,adds,adds,'stop']
    elif label in ('expires','finite-unfocused-snapshot'):last=partial
    elif label=='arrives':first=partial
    elif label in ('empty-camera','layer-one'):first=last=[adds]*5
    elif label=='interrupt-expires':last=[adds]*5
    elif label.startswith('penalty-weapon-'):
        first=last=['penalty']*5
        if label=='penalty-weapon-absent':first=last=['penalty','','','','']
        elif label=='penalty-weapon-expires':last=['penalty','','','','']
        elif label=='penalty-weapon-same-frame-destruction':last=['']*5
    if label in ('numeric-cache-live-marker','numeric-cache-epoch'):
        first=['','','','','penalty'];last=['penalty']*5
    assert rows[0]['aims']==first and rows[-1]['aims']==last,(case['name'],'native first/last aims',rows[0],rows[-1])
    shots=[2,2,0,0,0] if label.startswith('penalty-weapon-') else [0]*5
    if label=='numeric-cache-live-marker':shots=[3,0,0,0,0]
    if label=='numeric-cache-epoch':shots=[3,3,0,0,0]
    if label.startswith('numeric-cache-'):
        damage=[6600,6000,6600] if label=='numeric-cache-live-marker' else [6600,6000,6600,6600,6600,6600]
        assert [r['damage'] for r in native['projectile_shots']]==damage,(case['name'],'numeric cache versus live marker')
    assert native['shots']==shots,(case['name'],'aim-only versus physical scope')
    return dict(verified=True,reference_model_gap=False,aim_frames=len(rows),physical_shots=sum(shots))
