"""Current native threshold semantics, with actual capped activation receipts."""
def verify(case,native):
    scene=case['catalogue_profile']['scene_witness']['scenario']
    assert scene in ('control','first','two','exhausted'),'Unknown original threshold scene'
    from world_original_support_native import selected
    rows=selected(case);assert len(rows)==2
    effects=case['effects'];buff=next(i for i in rows if effects[i]['stat']=='invincible');heal=next(i for i in rows if effects[i]['stat']=='heal_hp_pct')
    receipt=native['support_conditions'];events=receipt['activations'];attempts=receipt['attempts']
    expected={'control':0,'first':1,'two':2,'exhausted':2}[scene]
    for e in [*events,*attempts]:
        assert e['row'] in rows and e['owner']==case['owners'][e['row']],'Original threshold identity required'
    for row in rows:
        assert sum(e['row']==row for e in events)==expected,'Only successful original activations count'
        calls=[e for e in attempts if e['row']==row]
        assert len(calls)==(3 if scene=='exhausted' else expected),'Original threshold call count required'
        for index,e in enumerate(calls):
            assert (e['before'],e['after'])==(min(index,2),min(index+1,2)),'Per-source trigger budget must be capped'
            assert e['hp_pct'][2 if index!=1 else 3]<50,'Literal injury must cross the defender threshold'
    heals=[e for e in receipt['heals'] if e['row']==heal]
    assert len(heals)==expected,'No recovery dispatch after the original budget is exhausted'
    for event in receipt['heals']:
        i=event['row'];assert type(i) is int and 0<=i<len(effects)
        assert event['owner']==case['owners'][i] and event['stat']==effects[i]['stat'] and event['name']==effects[i]['name'],'Original recovery identity required'
    hits=native['battle']['hits'];assert not any(h['down'] for h in hits)
    assert native['burst_controls']['ticks'][-1]['cycles']>=1
    assert len(hits)=={'control':0,'first':2,'two':4,'exhausted':6}[scene]
    if not expected:return
    by_name={h['pattern']:h for h in hits}
    first=by_name['first-defender'];protected=by_name['first-protected']
    assert first['owner']==2 and first['hp']>0
    assert protected['owner']==2 and protected['damage']>0 and all(protected[k]==0 for k in ('hp','shield','cover','decoy')),'Original invincibility must suppress real incoming damage'
    assert heals[0]['after']['hp'][2]>heals[0]['before']['hp'][2] and heals[0]['after']['hp'][3]==heals[0]['before']['hp'][3]
    if expected==2:
        assert by_name['second-defender']['owner']==3 and by_name['second-defender']['hp']>0
        second=heals[1]
        assert second['before']['hp_pct'][2]>50 and second['before']['hp_pct'][3]<50
        # The pinned instant handler heals both resolved class recipients.
        # Do not confuse this observation with per-target runtime buff gates
        # or a verified in-game rule.
        assert all(second['after']['hp'][i]>second['before']['hp'][i] for i in (2,3)),'Preserve current native class-wide instant recovery'
    if scene=='exhausted':
        assert by_name['third-crossing']['hp']>0 and by_name['exhausted']['hp']>0,'After expiry and budget exhaustion incoming damage must reach HP'
