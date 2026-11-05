"""Coordinates choose kinds, depth order and actual landings; no GPU inference."""
def verify(case,native):
    c=case['contract'];events=native['parts_skill_events'];packets=[x for x in events if x['kind']=='packet'];selection=native['coordinate_skill']
    assert [x['kind'] for x in events]==c['event_kinds']
    assert native['damage']==c['damage'],(case['name'],'damage',native['damage'])
    assert [(x['target'],x['damage']) for x in packets]==[tuple(x) for x in c['packets']],(case['name'],'packet order',packets)
    assert all(x['extra']==bool(x['target']) and x['part']=='' for x in packets)
    assert sum(x['kind']=='named-hit' for x in events)==c['notices'] and native['gauge']==0
    assert native['parts_skill_accounting']['interrupt_damage']==c['interrupt']
    assert [s['targets'] for s in selection['selections']]==c['selected']
    assert [s['geometry'] for s in selection['selections']]==c['geometry']
    assert selection['unchanged_geometry_reused'] and selection['reuse_checks']>0 and selection['snapshots']
    if c['marker']:
        assert all('stop' not in s['targets'] for s in selection['selections'])
        assert all(s['targets']==[name for name,kind in zip(s['geometry'],s['kinds'],strict=True) if kind=='parts'] for s in selection['selections'])
    if case.get('observe_selection_liveness'):assert [s['retired_targets'] for s in selection['selections']]==[[],['near']]
    if 'hp' in c:assert [a['hp'] for a in native['allies']]==c['hp']
    if c.get('retired_same_cast'):
        rows=[r for r in selection['target_accounting'] if r['kind']=='parts']
        assert [r['before_alive'] for r in rows]==[True,True,False,False]
        assert [r['pool_damage_delta'] for r in rows]==[3000,3000,0,0]
        assert [r['pool_hits_delta'] for r in rows]==[1,1,0,0]
        assert sum(r['event']=='destroy' for r in native['boss_log'])==2
    return dict(verified=True,native_coordinate_path=True,packets=len(packets),casts=len(selection['selections']),interrupt_accounting_verified=True,depth_order_verified=True,geometry_cache_reuse_verified=True,reference_model_gap=False,gpu_supported=False,full_character_verified=False)
