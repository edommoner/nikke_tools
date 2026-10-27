"""Exact named capacity/lifetime evidence does not certify lock targeting."""
from portable_heavyarms_lock_cases import source_definitions
from effect_target_count_policy import MODEL

def verify(case,native):
    r=native['effect_target_count'];assert r['model']==MODEL and r['transparent'] is True
    assert r['original_definitions']==source_definitions() and len(r['original_definitions'])==25 and r['prepared_effect_count']>=25
    assert r['selection_consumer_connected'] is False and r['gpu_supported'] is False
    events=r['events'];assert events and any(e['kind']=='consume' for e in events)
    activations=0;retired=0
    for event in events:
        q=event['query'];assert q==dict(model=MODEL,base_count=5,additional_targets=10. if q['capacity']==15 else 0.,capacity=q['capacity'],spatial_selection_verified=False,gpu_supported=False)
        assert q['capacity'] in (5,15)
        if event['kind']=='activate':assert q['capacity']==15;activations+=1
        else:
            assert event['kind']=='consume';old=event['before'];assert old['capacity'] in (5,15)
            if old['capacity']==15 and q['capacity']==5:retired+=1
    if case['body']['duration']==30:assert activations>0 and retired>0,'No actual burst modifier consumption observed'
    return dict(verified=True,reference_model_gap=True,original_definitions=25,named_target_count_query_verified=True,
        actual_activation_events=activations,actual_final_shot_removals=retired,selection_consumer_connected=False,gpu_supported=False)
