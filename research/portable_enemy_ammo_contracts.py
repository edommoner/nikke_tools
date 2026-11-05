"""Original Velvet effects must control real, generation-owned enemy shots."""
from collections import Counter


def verify(case,native):
    identity=native['original_input_identity'];data=native['enemy_ammo'];scenario=case['contract']['scenario']
    assert identity==dict(definitions=76,effects_owners_weapons_chars_config_seed_verified=True,added_effects=0)
    assert data['operator_code_reused'] and data['capacity_model']=='fixed-declared'
    charges=data['charges'];attempts=data['attempts'];generations=data['generations'];reloads=data['reloads']
    assert len(charges)==2 and charges[0]['time']==0 and 3<charges[1]['time']<4
    expected=-2.95 if scenario=='level1' else -5.
    for charge in charges:
        assert charge['name']=='탄환 가져오기 2' and charge['caster']=='벨벳' and charge['value']==expected
        assert len(charge['completion'])==1
        done=charge['completion'][0]
        assert done['event']=='event:'+charge['name'] and done['time']==charge['time']
        assert done['remaining']=={r['label']:r['after'] for r in charge['targets']},'Named completion must follow the complete recipient loop'
        for r in charge['targets']:
            assert r['capacity']==16 and r['change']==(0 if scenario=='level1' or r['before']==0 else -1)
            assert 0<=r['after']<=r['capacity']
    known={tuple(r['actor']) for r in generations}
    assert len(known)==len(generations)
    for attempt in attempts:
        assert tuple(attempt['actor']) in known
        assert attempt['status'] in ('fired','empty','reloading')
        assert attempt['after']==attempt['before']-int(attempt['status']=='fired')
        if attempt['status']=='empty':assert attempt['before']==0
    fired=[r for r in attempts if r['status']=='fired']
    hits=native['battle']['squad_hits']
    assert len(hits)==len(fired)*5 and all(h['damage']==1. and not h['down'] for h in hits)
    actual=Counter((h['t'],h['pattern'],h['by']) for h in hits)
    expected_hits=Counter()
    for r in fired:
        source='' if r['actor'][0]==0 else r['label'].removeprefix('__enemy__:')
        expected_hits[r['time'],r['pattern'],source]+=5
    assert actual==expected_hits,'Original incoming-damage receipts must match only ammo-admitted attempts'
    assert any(h['hp']>0 for h in hits),'Must reach actual original squad HP, not only a magazine counter'
    for r in reloads:
        assert r['kind'] in ('start','complete')
        if r['kind']=='complete':
            assert r['after']==16 and 0<=r['time']-r['deadline']<1/60+1e-12
    if scenario in ('level10','level1','body'):
        assert len(generations)==3 and all(r['actor'][2]==1 for r in generations)
        assert any(r['kind']=='complete' for r in reloads)
        assert len(attempts)==(25 if scenario=='body' else 50),'Blocked attempts must not retime original scheduling'
    if scenario=='late-empty':assert charges[0]['targets']==[] and len(generations)==2 and all(abs(r['time']-2)<1/60 for r in generations)
    if scenario=='dead':
        assert charges[1]['targets']==[] and len(attempts)==2 and not reloads
        assert all(not r['alive'] for r in data['final'])
    if scenario=='renewal':
        assert len(generations)==4 and {r['actor'][2] for r in generations}=={1,2}
        assert all(r['initial']==3 for r in generations)
        assert len(attempts)==32
        assert all(r['before']==3 for r in attempts if r['actor'][2]==2 and r['index']==0),'New generation starts from declared initial rounds'
    return dict(verified=True,reference_model_gap=True,original_definitions=76,
        native_percentage_operator_reused=True,real_incoming_HP=True,attempts=len(attempts),fired=len(fired),
        original_scheduled_attempts_retained=True,generations=len(generations),
        capacity_model='fixed-declared',gpu_wire_connected=False,gpu_supported=False,in_game_rules_verified=False)
