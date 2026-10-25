"""Real live mode and health effects alongside exact shared RNG replay."""
def verify(case,native):
    from portable_coordinate_sampled_burst_contracts import verify as parent
    answer=parent(case,native);shots=native['sampled_live_shots'];health=native['sampled_health_returns']
    assert shots and all(1<=r['pellets']*r['muzzles']<=1024 for r in shots)
    label=case['name'].rsplit('/',1)[1]
    if label=='mode-expired-before-entry':assert not any(r['mode'] for r in shots)
    elif label.startswith('mode-') or label=='lifesteal-packets':assert any(r['mode'] for r in shots)
    if label=='mode-shotgun-muzzles':assert any(r['mode'] and (r['pellets'],r['muzzles'])==(4,3) for r in shots)
    if label=='mode-charge-muzzles':assert any(r['mode'] and r['muzzles']==2 for r in shots)
    if label.startswith('heal-'):assert any(r['kind']=='handle_heal_hp_pct' for r in health)
    if label=='cover-repair':assert any(r['kind']=='handle_cover_heal_pct' for r in health)
    if label=='lifesteal-packets':assert health[-1]['hp'][0]>2000
    answer.update(live_shots=len(shots),mode_shots=sum(r['mode'] for r in shots),health_returns=len(health),healing_handlers=sum(r['kind']=='handle_heal_hp_pct' for r in health),cover_handlers=sum(r['kind']=='handle_cover_heal_pct' for r in health))
    return answer
