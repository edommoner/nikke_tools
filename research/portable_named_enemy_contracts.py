"""Literal candidate order, exact opaque name and fallback-before-delivery."""
from portable_named_enemy_cases import BOSS

def verify(case,native):
    c=case['contract'];o=native['named_enemy'];rank=o['rankings'];recipients=o['recipients'];target='enemies_with_buff:'+c['mark_name']
    assert len(rank)==c['rank_calls'] and len(recipients)==c['recipient_calls'],(case['name'],'call counts',o)
    assert [r['picked'] for r in recipients]==(c['picked'] if c['recipient_calls'] else [])
    for i,r in enumerate(recipients):
        assert r['target']==target and r['owner']==0
        assert abs(r['time']-[0,7/60,13/60][i])<1e-12
    for i,r in enumerate(rank):
        step=c['rank_steps'][i];checks=r['checks'];pool=c['pools'][i]
        assert r['target']==target and r['owner']==0
        assert [p['identity'] for p in checks]==pool,(case['name'],'pool order')
        assert all(p['name']==c['mark_name'] for p in checks),(case['name'],'opaque name')
        assert [p['identity'] for p in checks if p['present']]==c['present'][step],(case['name'],'membership')
        assert r['order']==c['picked'][step] and r['count']==len(r['order'])
        assert r['order']==(c['present'][step] or [BOSS]),(case['name'],'boss fallback')
    assert native['rng']['draws']==0
    assert native['named_state']['allied_carriers']==[],(case['name'],'enemy observations must not become allies')
    return dict(verified=True,reference_model_gap=False,rankings=len(rank),recipient_resolutions=len(recipients),membership_checks=sum(len(r['checks']) for r in rank),consumer=c['kind'],opaque_name=c['mark_name'],picked=c['picked'])
