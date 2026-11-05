"""Actual queue birth/consumption and shared MT/critical contracts."""
def verify(case,native):
    from portable_coordinate_sampling_contracts import verify as sampling
    answer=sampling(case,native);ordinary=[r for r in native['sampled_skill_damage'] if not r['target']];legacy=native['sampled_legacy_damage'];batches=native['sampled_burst_batches']
    uniforms=[r for r in native['sampled_draws'] if r['kind']=='native-uniform' and r['caller']=='_factor3']
    assert len(uniforms)==len(native['physical_pellets'])+len(ordinary)+len(legacy)
    for row in legacy:
        batch=batches[row['batch']];entry=batch['entries'][row['index']]
        assert entry['mode']==1 and (entry['owner'],entry['name'],entry['hits'])==(row['owner'],row['name'],row['hits'])
        assert row['time']==batch['time'] and row['crit_fraction']==float(row['critical'])
    resolved=[r for r in native['full_burst_landing_observation']['calls'] if r['resolved']]
    assert all(r['full'] for r in resolved)
    answer.update(legacy_body_calls=len(legacy),ordinary_body_calls=len(ordinary),optin_resolved_calls=len(resolved),pending_batches=len(batches),critical_uniforms=len(uniforms),actual_queue_packets=len(native['landed_packets']))
    return answer
