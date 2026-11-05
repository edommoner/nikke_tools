"""Exact named capacity/lifetime evidence does not certify lock targeting."""
from portable_heavyarms_lock_cases import source_definitions
from effect_target_count_policy import MODEL

def _query(q):
    assert type(q['capacity']) is int and q['capacity'] in (5,15)
    assert type(q['additional_targets']) in (int,float)
    assert q['spatial_selection_verified'] is False and q['gpu_supported'] is False
    assert q==dict(model=MODEL,base_count=5,additional_targets=10. if q['capacity']==15 else 0.,capacity=q['capacity'],spatial_selection_verified=False,gpu_supported=False)

def verify(case,native):
    r=native['effect_target_count'];assert r['model']==MODEL and r['transparent'] is True
    assert r['original_definitions']==source_definitions() and len(r['original_definitions'])==25 and r['prepared_effect_count']>=25
    assert r['selection_consumer_connected'] is False and r['gpu_supported'] is False
    events=r['events'];assert events and any(e['kind']=='consume' for e in events)
    activations=0;retired=0;remaining=0;activated_at=None
    for event in events:
        q=event['query'];_query(q)
        if event['kind']=='activate':
            assert q['capacity']==15;activations+=1;remaining=2;activated_at=event['time']
        else:
            assert event['kind']=='consume';old=event['before'];_query(old)
            assert old['capacity']==(15 if remaining else 5)
            if remaining and event['time']!=activated_at:remaining-=1
            assert q['capacity']==(15 if remaining else 5),'Actual shot lifetime differs from source2'
            if old['capacity']==15 and q['capacity']==5:retired+=1
    if case['body']['duration']==30:assert activations>0 and retired>0,'No actual burst modifier consumption observed'
    return dict(verified=True,reference_model_gap=True,original_definitions=25,named_target_count_query_verified=True,
        actual_activation_events=activations,actual_final_shot_removals=retired,selection_consumer_connected=False,gpu_supported=False)
