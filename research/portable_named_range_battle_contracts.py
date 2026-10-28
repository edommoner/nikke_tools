"""Real original-profile skill packets must reach the declared actor set."""
from portable_named_range_battle_cases import OWNER,SUPPORT,EFFECT

def verify(case,native):
    identity=native['original_input_identity'];data=native['named_range_battle'];casts=data['casts'];landings=data['landings'];scenario=case['contract']['scenario']
    assert identity['definitions']==87 and identity['effects_owners_weapons_chars_config_seed_verified'] and identity['added_effects']==0
    assert casts and len(landings)==len(casts)
    assert all(r['owner']==OWNER and r['effect']==EFFECT for r in casts)
    assert any(r['percent']==500. and r['additional_targets']==1. and r['capacity']==3 for r in casts)
    assert all(r['factor']==1.+r['percent']/100. and r['radius']==r['base_radius']*r['factor'] for r in casts)
    assert all(len(r['recipients'])<=r['capacity'] and len({tuple(h['handle']) for h in r['recipients']})==len(r['recipients']) for r in casts)
    assert all(0<=r['cast']<len(casts) and r['created']==casts[r['cast']]['time'] and r['landed']>=r['created'] and r['damage']>0 for r in landings)
    assert all(r['recipients']==[x['label'] for x in casts[r['cast']]['recipients']] for r in landings),'No death between creation and landing in these four original worlds'
    if scenario=='expanded':
        assert any(r['percent']==0 and len(r['recipients'])==2 for r in casts)
        assert any(r['percent']==500. and len(r['recipients'])==3 for r in casts)
    elif scenario=='small-base-control':
        assert all(len(r['recipients'])<=2 for r in casts)
        assert any(r['percent']==500. and r['radius']==.6000000000000001 for r in casts)
    elif scenario=='late-spawn':
        assert any(r['time']<7. and len(r['recipients'])==1 for r in casts)
        assert any(r['time']>=7. and len(r['recipients'])==3 for r in casts)
    elif scenario=='retirement':
        assert all([h['label'] for h in r['recipients']]==['__enemy__'] for r in casts)
        assert native['battle']['add_total']==3
    else:raise AssertionError('Unreviewed named radial battle scenario')
    return dict(verified=True,reference_model_gap=True,original_definitions=87,original_support_profile=SUPPORT,casts=len(casts),landings=len(landings),expanded_casts=sum(r['percent']==500 for r in casts),max_recipients=max(len(r['recipients']) for r in casts),existing_actor_registry_and_HP=True,existing_damage_and_events=True,cast_snapshot_connected=True,actual_battle_delivery_connected=True,gpu_wire_connected=False,metal_verified=False,current_cuda_verified=False,gpu_supported=False,historical_canonical_equivalence=False,in_game_rules_verified=False)
