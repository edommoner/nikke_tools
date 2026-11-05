"""Native notification contract; the small physical GPU entry rejects cover."""
def verify(case,native):
    expected=case['cover_contract'];events=native['cover_notifications']
    covers=[e for e in native['clear_events'] if e['event']=='event:cover']
    assert len(events)==(0 if expected['blocked'] else 1)
    assert all(e['owner']==expected['owner'] and e['charging'] is False for e in events)
    own=expected['owner']==case['lock_owner'] and not expected['blocked']
    assert len(covers)==int(own)
    for e in native['clear_events']:
        assert e['after']['handles']==[]
        assert e['after']['revision']==e['before']['revision']+1
    if own:
        event=covers[0];assert event['time']==events[0]['time']
        assert bool(event['before']['handles']) is not expected['empty']
        # New pulses must reacquire after the real cover entry; no cached lock
        # may survive into the next emission. Native firing still controls time.
        next_shot=next(s for s in native['lock_shots'] if s['time']>=event['time'])
        pulses=[p for p in native['lock_pulses'] if event['time']<p['time']<=next_shot['time']]
        assert len(next_shot['handles'])==len(pulses)>0
        assert next_shot['revision']==event['after']['revision']+len(pulses)
    attacks=[e for e in native['clear_events'] if e['event']=='on_attack']
    assert len(attacks)==len(native['lock_shots'])>0
    for e,shot in zip(attacks,native['lock_shots'],strict=True):
        assert e['time']==shot['time'] and e['before']['handles']==shot['handles']
        assert e['before']['revision']==shot['revision']
    return dict(verified=True,reference_model_gap=True,native_cover_notifications=len(events),
        owner_cover_clears=len(covers),native_attack_clears=len(attacks),
        actual_native_controls=True,charging_cancelled_before_cover_notification=True,
        spatial_selection_verified=False,full25_verified=False,gpu_supported=False)
