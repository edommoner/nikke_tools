"""Literal observed lifetime outcomes; no alternate healing implementation."""
TAKES={'ended-down-revive':[0],'live-self-down-revive':[0],'persistent-self-down-revive':[1000],
'shared-live-down-revive':[1000],'shared-collect-while-owner-down':[1500],'other-owner-recipient-down':[0],
'other-owner-ended-kept':[1000],'persistent-owner-still-down':[],'shared-owner-still-down':[],
'ended-owner-still-down':[],'other-recipient-owner-down':[1000],'shared-expired-while-owner-down':[0]}
def verify(case,native):
    kind=case['contract']['kind'];events=native['healing_charge']['events'];takes=[e for e in events if e['kind']=='take']
    assert [e['value'] for e in takes]==TAKES[kind],(kind,[e['value'] for e in takes],TAKES[kind])
    assert native['allies'][0]['down']==('still-down' in kind),(kind,native['allies'][0])
    if kind=='persistent-owner-still-down':
        final=native['healing_charge']['final'];assert len(final)==1 and final[0]['active'] and final[0]['current']==1000
    if kind=='shared-owner-still-down':
        final=native['healing_charge']['final'];assert len(final)==1 and final[0]['active'] and final[0]['current']==1500
    if kind=='ended-owner-still-down':assert not native['healing_charge']['final']
    return dict(verified=True,declared_model=True,in_game_rules_verified=False,takes=TAKES[kind],original_pool_retained=kind.startswith(('persistent','shared')))
