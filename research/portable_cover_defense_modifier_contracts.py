"""Real original received modifiers must reach the cover layer, without probability edits."""
def verify(case,native):
    c=case['contract'];rows=native['cover_defense']['receipts'];hits=native['battle']['hits']
    assert c['definitions']==69 and c['names'][1]=='노아'
    assert native['original_input_identity']==dict(definitions=69,chars_config_seed_weapon_verified=True,authored_metadata_overrides=False,authored_delays_overrides=False,original_controls_preserved=False,declared_manual_sequences_applied_after_identity_check=True)
    assert len([h for h in hits if h['pattern']=='noah-prime' and h['owner']==1])==64,'Every actual Noah priming hit must execute'
    assert len({(h['time'],h['pattern'],h['owner']) for h in hits})==len(hits)
    assert not any(h['down'] for h in hits),'This modifier witness must retain every original receiver'
    for who,ally in enumerate(native['battle']['allies']):
        assert ally['received_damage']==sum(h['hp'] for h in hits if h['owner']==who),'Canonical compensated received aggregate must retain every actual HP term'
    assert all(h['pattern'] in {p['id'] for p in case['patterns'][1:]} for h in hits)
    for p in case['patterns'][2:]:
        who=int(p['spec']['target'].removeprefix('slot:'))-1
        assert len([h for h in hits if h['pattern']==p['id'] and h['owner']==who])==1,'Every literal phase target must land'
    assert len(rows)==sum(h['cover']>0 for h in hits)
    activations=native['received_conditions']['activations']
    assert len(activations)==3 and all(a['row']==c['noah_source_row'] and a['owner']==1 for a in activations),'Actual original Noah probability source must activate three times at seed 4301'
    assert all(any(a['time']<=r['time']<a['time']+10. for a in activations) for r in rows if r['received_snapshot']==-8.),'Nonzero snapshots must have a live original source'
    phase_rows=[r for r in rows if r['time']>7]
    assert phase_rows and {r['coefficient'] for r in phase_rows}==set(c['coefficients'])
    assert any(r['received_snapshot']==-8. for r in phase_rows),'Original probability source must actually produce a nonzero received snapshot'
    assert all(r['received_snapshot'] in (0.,-8.) for r in rows)
    assert any(r['effective_defense']>r['base_defense'] and r['received_snapshot']==-8. for r in phase_rows),'Cover DEF and received modifier must actually overlap'
    for r in rows:
        assert r['base_defense']==next(b['base_defense'] for b in case['cover_defense'] if b['name']==r['name'])
        amount=max(r['attack']-r['effective_defense'],0.)*r['coefficient']/100.
        assert r['quantity']==max(amount*max(0.,1.+r['received_snapshot']/100.),1.)
        assert r['shared_quantity']==r['quantity']/r['divisor'] and r['applied']==min(r['hp_before'],r['shared_quantity']) and r['hp_after']==r['hp_before']-r['applied']
        matching=[h for h in hits if h['time']==r['time'] and h['owner']==c['names'].index(r['name'])]
        assert len(matching)==1 and matching[0]['cover']==r['applied']
        source=next(p for p in case['patterns'] if p['id']==matching[0]['pattern'])
        assert r['coefficient']==source['spec']['coeff'],'Every cover snapshot must retain its actual source coefficient'
        assert r['divisor']==len([h for h in hits if h['time']==r['time'] and h['pattern']==matching[0]['pattern']]),'All living original split recipients must retain the frozen divisor'
    if c['pierce']:assert any(h['hp']>0 and h['cover']>0 for h in hits)
    return dict(verified=True,declared_model=True,original_definitions=69,cover_receipts=len(rows),incoming_rows=len(hits),original_probability_activations=len(activations),nonzero_received_receipts=sum(r['received_snapshot']!=0 for r in rows),coefficients=sorted({r['coefficient'] for r in rows}),gpu_supported=False,in_game_rules_verified=False)
