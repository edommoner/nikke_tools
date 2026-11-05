"""Bind actual body/target calculations to the independently replayed MT stream."""
def verify(case,native):
    from portable_coordinate_sampling_contracts import verify as sampling
    result=sampling(case,native);rows=native['sampled_skill_damage'];bodies=[r for r in rows if not r['target']]
    draws=[r for r in native['sampled_draws'] if r['kind']=='native-uniform' and r['caller']=='_factor3']
    assert len(draws)==len(native['physical_pellets'])+len(bodies),'One critical uniform per physical/skill body; no target reroll'
    body=None
    for row in rows:
        assert row['crit_fraction']==float(row['critical'])
        if not row['target']:body=row
        else:
            assert body is not None and all(row[k]==body[k] for k in ('owner','time','name','critical','crit_fraction')),'Target critical override must reuse its body'
    result.update(skill_body_calls=len(bodies),skill_target_reuses=len(rows)-len(bodies),critical_uniforms=len(draws),actual_queue_packets=len(native['landed_packets']))
    return result
