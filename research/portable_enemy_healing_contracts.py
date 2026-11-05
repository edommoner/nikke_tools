"""Original Anne reduction must change real source-owned ADD health."""
import json
from functools import lru_cache
from pathlib import Path

@lru_cache(None)
def original_effect():
    p=Path(__file__).resolve().parent/'upstream/nikke-calc-master/data/parsed_skills.json'
    rows=json.loads(p.read_text())['앤 : 미라클 페어리']
    return next(e for e in rows if e.get('stat')=='heal_received_pct' and e.get('target')=='all_enemies')

def verify(case,native):
    c=case['contract'];identity=native['original_input_identity'];data=native['enemy_healing'];receipts=data['receipts']
    assert identity['definitions']==69 and identity['effects_owners_weapons_chars_config_seed_verified'] and identity['added_effects']==0
    assert len(data['sources'])==4 and len(receipts)==8
    assert len({(r['node'],r['generation']) for r in data['sources']})==4
    assert all(r['source_generation']==1 and r['actor'][0]==5 for r in receipts)
    expected_scores={name:round(data['final_scored_damage'].get(name,0.)) for name in native['battle']['add_char_total']}
    assert native['battle']['add_char_total']==expected_scores
    assert native['battle']['add_total']==sum(expected_scores.values()) and native['battle']['add_overkill']==round(data['final_overkill']),'Preserve canonical per-owner final rounding separately from raw health credit'
    healed=[r for r in receipts if r['status']=='healed']
    if c['scenario']=='dead':
        assert not healed and all(r['status']=='dead-or-inactive' for r in receipts)
        assert native['battle']['add_total']==2,'Dead ADDs must not revive or accept scored damage again'
    else:
        if c['scenario']=='fractional-death':
            assert 4<=len(healed)<8 and any(r['status']=='dead-or-inactive' for r in receipts)
            assert any(not float(v).is_integer() for v in data['final_scored_damage'].values()) and not float(data['final_overkill']).is_integer(),'Fractional health clipping must preserve actual unrounded scored damage and overkill'
        else:assert len(healed)==8
        for row in healed:
            assert row['requested']==row['base_amount']*row['multiplier']
            assert row['applied']==min(row['requested'],row['dealt_before'])
            assert row['dealt_after']==row['dealt_before']-row['applied']
            assert row['hp_before']==row['max_hp']-row['dealt_before'] and row['hp_after']==row['max_hp']-row['dealt_after']
            assert 0<=row['hp_before']<=row['hp_after']<=row['max_hp']
            assert row['hits_before']==row['hits_after'] and row['scored_before']==row['scored_after'],'Healing changes health, not existing hit or scored-damage accounting'
        expected=max(0.,1.+original_effect()['values'][str(c['skill_level'])]/100.)
        reduced=[r for r in healed if r['multiplier']==expected]
        assert reduced and any(r['multiplier']==1. for r in healed)
        assert all(any(f['name']==original_effect()['name'] and f['visible'] for f in r['quantity_fields']) for r in reduced)
        assert any(r['effective_gain']>0 for r in reduced)
        if c['scenario']=='capped':assert all(r['dealt_after']==0 and r['applied']<=r['requested'] for r in healed)
        else:assert all(r['applied']<r['base_amount'] for r in reduced)
        if c['renewal']:
            fresh=[r for r in healed if r['actor'][2]==2 and r['excluded_stale_fields']]
            assert fresh and all(r['multiplier']==1. for r in fresh)
            assert all(any(f['actor'][2]==1 and f['expires_at']>r['time'] for f in r['excluded_stale_fields']) for r in fresh),'Still-live old-generation reduction cannot affect the new ADD'
    return dict(verified=True,reference_model_gap=True,original_definitions=69,original_heal_reduction_consumed=bool(healed),
        healing_attempts=len(receipts),live_queries=len(healed),actual_heals=sum(r['effective_gain']>0 for r in healed),source_nodes=len(data['sources']),
        existing_HP_and_generations=True,scored_damage_unchanged_by_heal=True,
        gpu_wire_connected=False,gpu_supported=False,historical_canonical_equivalence=False,in_game_rules_verified=False)
