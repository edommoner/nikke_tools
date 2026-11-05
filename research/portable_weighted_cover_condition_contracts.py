"""The condition must become true and the original heal must change real HP."""
from portable_weighted_battle_contracts import verify as original
def verify(case,native):
    result=original(case,native);rows=native['conditional_heals']
    assert rows and all(r['cover_hp']==0. for r in rows)
    assert any(r['hp_after']>r['hp_before'] for r in rows),'Broken-cover predicate must actually heal the original owner'
    effect=next(r['effect'] for r in case['contract']['original_markers'] if r['effect']['target']=='self_cover')
    assert effect['stat']=='received_dmg_split'
    result.update(original_broken_cover_condition_heals=len(rows),positive_hp_heals=sum(r['hp_after']>r['hp_before'] for r in rows))
    return result
