"""Literal witnesses plus independent native receipt/group consistency."""
def verify(case,native):
    assert native['reference_kind']=='deterministic-common-cpu'
    groups=native['groups'];shots=native['group_shots'];notices=native['group_notices'];receipts=native['group_receipts']
    label=case['name'].split('/')[-1]
    assert len(groups)==len(shots)>0
    expected={
        'occlusion-and-body':[[[0,0,1]]], 'full-front':[[]], 'interrupt-front':[[]],
        'two-muzzles-three-pellets':[[[0,0,1]]], 'retirement':[[[0,0,1]]]*3,
        'body-without-targets':[[[0,0,1]]], 'pierce-reach':[[[0,0,1]]],
        'charge-pierce':[[[0,0,1]]], 'threshold-snapshot':[[],[[0,0,1]]],
        'add-retirement':[[[5,0,1],[5,1,1],[0,0,1]]], 'add-alive':[[[5,0,1]]],
        'child-target-body':[[[0,0,1]]], 'child-retired-adds':[[[5,0,1],[5,1,1],[0,0,1]]],
        'zero-damage-body':[[[0,0,1]]], 'two-owners':[[[0,0,1]]]*2,
        'group-buff-next-shot':[[[0,0,1]]]*2,
    }
    if label=='long-history':
        assert len(groups)>64 and all(g['targets']==[[0,0,1]] for g in groups)
    else:assert [g['targets'] for g in groups]==expected[label],(label,groups)
    for i,(g,shot) in enumerate(zip(groups,shots,strict=True),1):
        assert g['finished'] and g['identity']==shot['identity']==g['epoch']==i
        assert g['owner']==shot['owner'] and g['time']==shot['time']
        matching=[r for r in receipts if r['identity']==i]
        owned=[]
        for r in matching:
            assert r['owner']==g['owner'] and r['time']==g['time']
            if r['target'][0] in (0,5) and r['credit']>0 and r['outcome']!=0 and r['target'] not in owned:owned.append(r['target'])
        assert g['targets']==owned
        selected=[n for n in notices if n['key'][1]==i]
        assert [int(n['event'].split(':')[1]) for n in selected]==([1,2] if len(owned)>=2 else [1] if owned else [])
        assert all(n['targets']==owned and n['key']==[g['owner'],i,i] for n in selected)
    if label=='two-muzzles-three-pellets':assert len(native['physical_pellets'])==6 and shots[0]['packets']==12 and len(receipts)==6
    if label=='zero-damage-body':assert native['physical_pellets'][0]['packets'][0]['damage']==0 and len(receipts)==1
    if label=='threshold-snapshot':
        assert [s['packets'] for s in shots]==[6,12]
        assert [p['damage'] for p in native['physical_pellets'][-1]['packets']]==[0,7000]
    if label=='two-owners':assert len({g['owner'] for g in groups})==2
    if label.startswith('child-'):
        assert len(native['group_children'])==1
        assert native['group_children'][0]['targets']==groups[0]['targets']
        # Frozen group references include retired ADDs; child routing neither
        # resurrects them nor redirects their allocation to the surviving BODY.
        assert [r['target'] for r in native['group_child_landings']]==[[0,0,1]]
    else:assert not native['group_children'] and not native['group_child_landings']
    if label=='group-buff-next-shot':
        packets=native['physical_pellets'];assert packets[0]['packets'][0]['damage']<packets[-1]['packets'][0]['damage']
    return dict(verified=True,reference_model_gap=False,reference_kind='deterministic-common-cpu',groups=len(groups),expanded_packets=sum(s['packets'] for s in shots),receipts=len(receipts),notifications=len(notices),gpu_supported=False)
