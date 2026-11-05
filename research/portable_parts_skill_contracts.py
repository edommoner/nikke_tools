"""Independent literal totals and landed packet order, before GPU admission."""
def require(condition,case,label,actual):
    # These prerequisites also remain effective if used directly under -O.
    if not condition:raise AssertionError((case['name'],label,actual))


def verify(case,native):
    expected=case['contract'];events=native['parts_skill_events'];packets=[e for e in events if e['kind']=='packet'];notices=[e for e in events if e['kind']=='named-hit']
    require(native['damage']==expected['damage'],case,'damage totals',native['damage'])
    require([e['damage'] for e in packets]==expected['packet_damage'],case,'packet amounts',packets)
    require([e['part'] for e in packets]==expected['packet_parts'],case,'packet targets/order',packets)
    require(len(notices)==expected['named_hit_notices'],case,'named notifications',notices)
    require([e['kind'] for e in events]==expected['event_kinds'],case,'creation notices and ordered landing packets',events)
    require(all(e['owner']==0 for e in events),case,'original attacker',events)
    if 'hp' in expected:require([a['hp'] for a in native['allies']]==expected['hp'],case,'per-part lifesteal',native['allies'])
    if 'interrupt_damage' in expected:require(native['parts_skill_accounting']['interrupt_damage']==expected['interrupt_damage'],case,'interrupt outside damage total',native['parts_skill_accounting'])
    if 'packet_reach' in expected:require([(e['reach'],e['part_damage'],e['interrupt_reach'],e['interrupt_damage']) for e in packets]==expected['packet_reach'],case,'native packet metadata',packets)
    if 'packet_times' in expected:require([e['time'] for e in packets]==expected['packet_times'],case,'landing times',packets)
    if 'gauge' in expected:require(native['gauge']==expected['gauge'],case,'gauge',native['gauge'])
    if 'pending' in expected:require(native['pending_burst']==expected['pending'],case,'actual deferred path',native['pending_burst'])
    if 'lifecycle_opens' in expected:
        lifecycle=native['parts_skill_lifecycle']
        require([(e['pattern'],e['ordinal']) for e in lifecycle if e['kind']=='part-open']==expected['lifecycle_opens'],case,'fresh part generations',lifecycle)
        require([e['parts'] for e in lifecycle if e['kind']=='part-capture']==expected['lifecycle_captures'],case,'landed part capture groups',lifecycle)
        if 'lifecycle_kinds' in expected:require([e['kind'] for e in lifecycle]==expected['lifecycle_kinds'],case,'group mutation before child healing',lifecycle)
    result=dict(verified=True,packets=len(packets),named_notifications=len(notices))
    if expected.get('reference_model_gap'):result['reference_model_gap']=True
    return result
