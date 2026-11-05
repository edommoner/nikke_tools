"""Reuse the canonical accumulator-call observer with real coordinate packets."""
def observe(case):
    import engine_worker
    from world_damage_accum_native import capture
    from world_coordinate_physical_common import observe as common
    from world_frame_native import roster_names
    with capture(roster_names(case),identity_rows=True) as accumulation:result=common(case)
    trace=result.pop('skill_trace');result['damage_accumulation']=accumulation
    return result,trace
