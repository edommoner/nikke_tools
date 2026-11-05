"""Named carrier identity/stack/removal is narrower than spatial Lock On support."""
from portable_heavyarms_lock_cases import NAME,source_definitions
MARK='록 온'

def verify(case,native):
    observed=native['heavyarms_lock'];definitions=observed['original_definitions'];events=observed['events']
    assert definitions==source_definitions() and len(definitions)==25 and observed['prepared_effect_count']>=25
    marker=definitions[0];assert marker['stat']=='lock_on' and marker['name']==MARK and marker['max_stack']==5 and marker['duration']==-1 and marker['target']=='enemies_nearest:1'
    assert definitions[20]['stat']=='effect_target_count_add' and definitions[20]['target_effect']==MARK
    assert definitions[24]['target']=='all_projectiles'
    assert observed['transparent'] is True and observed['probe_queries_are_injected'] is True
    assert all(observed[k] is False for k in ('spatial_selection_verified','target_count_extension_verified','full25_typed_projectile_verified'))
    recipient=case.get('expected_marker_target','__enemy__')
    if recipient!='__enemy__':
        assert recipient=='__enemy__:lock-wave#1'
        assert case['body']['enemy']['patterns']==[dict(id='lock-wave',kind='summon',spec=dict(count=3,hp=1e30))]
    activations=[e for e in events if e['kind']=='activate'];removals=[e for e in events if e['kind']=='remove']
    assert activations and removals and any(e['before']['carriers'] for e in removals)
    for event in events:
        state=event['state'];queries=state['diagnostic_queries']
        if event['kind']=='activate':
            assert event['name']==MARK and len(state['carriers'])==1
            carrier=state['carriers'][0]
            assert carrier['caster']==NAME and carrier['targets']==[recipient] and carrier['expires']=='infinite'
            assert 1<=carrier['stack']<=5
            assert queries==dict(any_enemy=True,boss=recipient=='__enemy__',stack=carrier['stack'])
        else:
            assert event['kind']=='remove' and not state['carriers']
            assert queries==dict(any_enemy=False,boss=False,stack=0)
    stacks=[e['state']['carriers'][0]['stack'] for e in activations]
    assert stacks[0]==1 and 5 in stacks and any(b==1 and a>1 for a,b in zip(stacks,stacks[1:])),stacks
    natural=observed['natural_queries']
    assert len(natural)==case.get('expected_natural_queries',0)
    if recipient!='__enemy__':
        pool=['__enemy__']+['__enemy__:lock-wave#'+str(i) for i in (1,2,3)]
        assert len(natural)%4==0 and any(q['present'] for q in natural)
        for start in range(0,len(natural),4):
            batch=natural[start:start+4];assert [q['target'] for q in batch]==pool
            assert all(q['name']==MARK and type(q['present']) is bool for q in batch)
            assert all(not q['present'] for q in batch if q['target']!=recipient)
    return dict(verified=True,reference_model_gap=True,original_definitions=25,activations=len(activations),removals=len(removals),marker_recipient=recipient,natural_named_queries=len(natural),diagnostic_queries_are_injected=True,named_marker_lifecycle_verified=True,spatial_selection_verified=False,target_count_extension_verified=False,full25_typed_projectile_verified=False,gpu_supported=False)
