"""Original sampled-probability recovery needs both success and failure witnesses."""
def verify(case,native):
    scene=case['catalogue_profile']['scene_witness']['scenario']
    assert scene in ('control','self-chipped','self-wounded','ally-chipped'),'Unknown original probability scene'
    from world_original_support_native import selected
    selected_rows=selected(case);assert len(selected_rows)==1,'Original probability must remain unchanged'
    row=selected_rows[0];effect=case['effects'][row]
    assert effect['trigger']==dict(timing=['received_hit_count:1'],condition=['prob:5']),'Original probability must remain unchanged'
    receipt=native['support_conditions'];events=receipt['activations'];heals=receipt['heals']
    for event in events:
        assert event['row']==row and event['owner']==0,'Original probability source identity required'
    for event in heals:
        i=event['row'];assert type(i) is int and 0<=i<len(case['effects'])
        original=case['effects'][i]
        assert event['owner']==case['owners'][i] and event['stat']==original['stat'] and event['name']==original['name'],'Original heal source identity required'
    hit_heals=[e for e in heals if e['row']==row]
    assert len(events)==len(hit_heals),'Successful dispatches must match counted original activations'
    hits=native['battle']['hits'];expected=0 if scene=='control' else 65 if scene=='self-wounded' else 64
    assert len(hits)==expected,'Preserve all literal repeated incoming hits'
    assert not any(h['down'] for h in hits)
    assert native['burst_controls']['ticks'][-1]['cycles']>=1
    if scene=='control':assert not events,'Unhit caster cannot gain received-hit activations';return
    owner=2 if scene=='ally-chipped' else 0
    assert all(h['owner']==owner and h['hp']>0 for h in hits),'Real intended recipient must receive every hit'
    if scene=='ally-chipped':
        assert not events,'Ally hits must not trigger the caster-only probability'
        assert any(e['row']!=row and e['after']['hp'][2]>e['before']['hp'][2] for e in heals),'Original burst must actually recover the injured ally'
        return
    assert 0<len(events)<len(hits),'Original 5% source needs actual successes and failures'
    assert any(e['after']['hp'][0]>e['before']['hp'][0] for e in hit_heals),'Probability success must actually recover injured HP'
    assert all(any(abs(h['time']-e['time'])<1e-9 for h in hits) for e in events),'Probability activations must come from actual hit frames'
    if scene=='self-chipped':assert all(e['before']['hp_pct'][0]>90 for e in hit_heals),'High-HP condition control required'
    else:assert any(e['before']['hp_pct'][0]<90 for e in hit_heals),'Low-HP recovery condition must really execute'
