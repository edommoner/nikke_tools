"""Literal reload snapshot and control-composition witnesses, before GPU comparison."""
def verify(case,native):
    observed=native['coordinate_aim'];frames=observed['frames'];label=case['name'].split('/')[-1]
    assert frames and native['reference_kind']=='deterministic-common-cpu'
    if label.startswith('mode-'):
        start=.5-.4;end=start+.1
        assert all(f['aims'][0]['target']==('front' if start<=f['time']<end else '') for f in frames),label
        assert any(f['aims'][0]['target']=='front' for f in frames)
        assert any(r['owner']==0 for r in native['battle']['manual_control']['arbitration'])
    elif label.startswith(('base-single-clip','fixed-reload','clip31','capacity-and')):
        one=.1 if label=='fixed-reload-and-ratio' else .4
        spans=[r for r in observed['anchors'] if r['resolved'] is not None]
        assert spans and any(case['controls'][0]['aim'][0]['offset']-r['resolved'][1]>one*1.5 for r in spans),label
        assert any(f['aims'][0]['target']=='front' for f in frames),label
    elif label=='competing-hold-owner':
        assert frames[0]['owner']==1
        assert any(f['owner']==0 and f['full_burst'] for f in frames)
        assert any(r['request'] is not None and r['who']==1 and r['request'][1]==30 for r in observed['requests'])
    else:
        assert label.startswith(('manual-','aim-and-')),label
        assert all(f['owner']==0 and f['aims'][0]['target']=='front' for f in frames),label
        if 'pellet' in label or 'scatter' in label:
            assert len(native['physical_pellets'])>5,label
        if label=='aim-and-own-hold':assert any(f['full_burst'] for f in frames)
    return dict(verified=True,reference_model_gap=False,reference_kind='deterministic-common-cpu',gpu_supported=False,frames=len(frames))
