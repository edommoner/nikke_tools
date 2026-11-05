"""Final queued hits survive only their own canonical self-retirement."""
from collections import Counter


def verify(case,native):
    data=native['enemy_ammo'];scenario=case['contract']['scenario']
    assert native['original_input_identity']==dict(definitions=76,effects_owners_weapons_chars_config_seed_verified=True,added_effects=0)
    assert data['model']=='declared-enemy-magazine-final-queue-v1' and data['operator_code_reused']
    attempts=data['attempts'];retirements=data['retirements'];fired=[a for a in attempts if a['status']=='fired']
    assert len(data['charges'])==2
    for charge in data['charges']:
        assert charge['value']==-5. and charge['caster']=='벨벳'
        assert len(charge['completion'])==1
        assert charge['completion'][0]['remaining']=={r['label']:r['after'] for r in charge['targets']}
    receipts={(tuple(r['actor']),r['time']):r for r in retirements}
    assert len(receipts)==len(retirements)
    for a in attempts:
        assert a['status'] in ('fired','empty','reloading')
        assert a['after']==a['before']-int(a['status']=='fired')
        if a.get('retired_queue'):
            r=receipts[tuple(a['actor']),a['time']]
            assert a['label']==r['label'] and a['index'] in r['queued_indices']
    expected=Counter()
    for a in fired:expected[a['time'],a['pattern'],a['label'].removeprefix('__enemy__:')]+=5
    hits=native['battle']['squad_hits']
    assert Counter((h['t'],h['pattern'],h['by']) for h in hits)==expected
    assert all(h['damage']==1. and not h['down'] for h in hits)
    assert all(not r['alive'] for r in data['final'])
    if scenario in ('hp-before-shot','time-close'):assert not attempts and not retirements
    else:
        assert len(retirements)==(4 if scenario=='renewal' else 2)
        assert sum(bool(a.get('retired_queue')) for a in attempts)==(6 if scenario=='coincident' else 4 if scenario=='renewal' else 2)
        assert all(r['fired']==(3 if scenario in ('spaced','coincident','reload-final') else 1) for r in retirements)
    if scenario=='empty':assert not fired and all(a['status']=='empty' for a in attempts)
    if scenario=='reload-final':
        assert any(a['status']=='reloading' and a.get('retired_queue') for a in attempts)
        assert not fired and not any(r['kind']=='complete' for r in data['reloads'])
    if scenario=='renewal':
        assert {r['actor'][2] for r in retirements}=={1,2}
        assert len(data['generations'])==4 and all(r['initial']==16 for r in data['generations'])
    return dict(verified=True,reference_model_gap=True,original_definitions=76,
        attempts=len(attempts),fired=len(fired),self_retirements=len(retirements),
        final_queue_attempts=sum(bool(a.get('retired_queue')) for a in attempts),
        original_scheduler_and_percentage_operator_reused=True,
        retirement_depends_on_scheduled_attempts_not_ammo=True,
        full_battle_validation=True,gpu_wire_connected=False,gpu_supported=False,in_game_rules_verified=False)
