"""Check literal shot classes, native notice order and listener witnesses."""
def verify(case,native):
    c=case['contract'];owner=c['owner'];events=native['nonfull_charge']
    shots=[e for e in events if e['kind']=='shot' and e['owner']==owner]
    assert sum(not s['full'] for s in shots)==c['partial'],(case['name'],'partial count',shots)
    assert sum(s['full'] for s in shots)==c['full'],(case['name'],'full count',shots)
    assert len([e for e in events if e['kind']=='activate'])==c['activations'],(case['name'],'activations')
    assert [a['hp'] for a in native['allies']]==c['hp'],(case['name'],'health')
    physical=[p for p in native['projectile_shots'] if p['owner']==owner and p['mode']==1]
    assert [p['time'] for p in physical]==[s['time'] for s in shots],(case['name'],'physical shot identity')
    assert sum(p['owner']==owner and p['mode']!=1 for p in native['projectile_shots'])==c.get('auto_shots',0),(case['name'],'auto mode shots')
    for event,count in [('non_full_charge_fire',c['partial']),('full_charge_fire',c['full']),('full_charge',c['full'])]:
        assert sum(e.get('event')==event and e['owner']==owner for e in events)==count,(case['name'],'event count',event)
    muzzles=case['combat']['weapons'][owner].get('muzzles',1)
    for shot in shots:
        notices=[e['event'] for e in events if e['kind']=='notify' and e['owner']==owner and e['time']==shot['time']]
        expected=(['full_charge'] if shot['full'] else [])+['squad_ammo_consume','on_attack','full_charge_fire' if shot['full'] else 'non_full_charge_fire']+['hit_count']*muzzles+(['full_charge_hit']*muzzles if shot['full'] else [])
        assert notices==expected,(case['name'],'notification sequence',notices,expected)
    for position,e in enumerate(events):
        if e['kind']=='activate':
            assert e['owner']==owner,(case['name'],'caster ownership')
            before=[n for n in events[:position] if n['kind']=='notify']
            assert before and before[-1]['event'] in c.get('activation_events',('on_attack','non_full_charge_fire')) and before[-1]['time']==e['time'],(case['name'],'activation context')
    return dict(verified=True,reference_model_gap=False,partial_shots=c['partial'],full_shots=c['full'],activations=c['activations'])
