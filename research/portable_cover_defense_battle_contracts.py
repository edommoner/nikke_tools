"""Actual original cover damage, duration, break and shared protection receipts."""
def verify(case,native):
    c=case['contract'];data=native['cover_defense'];rows=data['receipts'];identity=native['original_input_identity'];hits=native['battle']['hits'];shared=c['scenario']=='shared-shield'
    assert identity==dict(definitions=c['definitions'],chars_config_seed_weapon_verified=True,authored_metadata_overrides=False,authored_delays_overrides=False,original_controls_preserved=False,declared_manual_sequences_applied_after_identity_check=True)
    assert c['definitions']==(67 if shared else 69),'All original roster definitions required'
    sources={p['id']:p for p in case['patterns'][1:]}
    expected={key:int(p['spec']['target'].removeprefix('slot:'))-1 for key,p in sources.items()}
    assert len(expected)==15 and all(h['pattern'] in expected for h in hits),'Only declared incoming sources may land'
    for pattern,who in expected.items():
        group=[h for h in hits if h['pattern']==pattern]
        if not group:
            assert c['scenario']=='broken' and any(h['owner']==who and h['down'] and h['time']<sources[pattern]['delay'] for h in hits),'Only actual prior death can suppress a declared target'
        else:
            recipients=({0,2,3} if shared and who in (0,2,3) else {who})
            assert len(group)==len(recipients) and {h['owner'] for h in group}==recipients,'Original sharing recipients required'
    for r in rows:
        assert r['base_defense']==next(b['base_defense'] for b in case['cover_defense'] if b['name']==r['name'])
        percentage=128.57 if 10<r['time']<15 and r['name'] in c['boosted_owners'] else 0.
        assert r['effective_defense']==r['base_defense']*(1.+percentage/100.)
        amount=max(r['attack']-r['effective_defense'],0.)*r['coefficient']/100.
        assert r['quantity']==max(amount*max(0.,1.+r['received_snapshot']/100.),1.)
        assert r['shared_quantity']==r['quantity']/r['divisor'] and r['applied']==min(r['hp_before'],r['shared_quantity']) and r['hp_after']==r['hp_before']-r['applied']
        matching=[h for h in hits if c['names'][h['owner']]==r['name'] and h['time']==r['time']]
        assert len(matching)==1 and matching[0]['cover']==r['applied'],'Original real cover subtraction must use the declared quantity'
    assert len(rows)==sum(h['cover']>0 for h in hits),'Every actual cover subtraction needs one receipt'
    if c['scenario']=='broken':
        assert len(hits)==13 and len(rows)==5 and all(r['hp_after']==0 for r in rows),'Original live cover must actually break'
        assert all(x['hp']==0 for x in native['battle']['covers'])
        assert any(h['hp']>0 and h['cover']==0 for h in hits if h['time']>10),'Broken cover cannot absorb later damage'
    else:
        assert len(hits)==(33 if shared else 15) and len(rows)==(16 if shared else 15)
        assert {r['name'] for r in rows if 10<r['time']<15 and r['effective_defense']>r['base_defense']}==set(c['boosted_owners']),'Original top-ATK three must receive the real active percentage'
        assert all(r['effective_defense']==r['base_defense'] for r in rows if r['time']<10 or r['time']>15),'Original expiry must restore the independent base'
    if c['scenario']=='phases':assert all(h['hp']==0 for h in hits)
    if c['scenario']=='pierce':assert all(h['hp']>0 and h['cover']>0 for h in hits),'Piercing must retain body damage separately'
    if shared:
        assert any(r['divisor']==3 for r in rows) and all(r['divisor'] in (1,3) for r in rows),'Original equal-sharing recipient loop must really execute'
        assert any(h['shield']>0 for h in hits),'Original shields must actually absorb before cover'
    return dict(verified=True,declared_model=True,original_definitions=c['definitions'],cover_receipts=len(rows),hits=len(hits),shared_receipts=sum(r['divisor']>1 for r in rows),actual_cover_breaks=sum(r['hp_after']==0 for r in rows),gpu_wire_connected=False,gpu_supported=False,in_game_rules_verified=False)
