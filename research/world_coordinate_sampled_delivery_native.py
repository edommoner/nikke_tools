"""Attach existing receipt groups to the real sampled weapon/health observer."""
def observe(case):
    import engine_worker
    from calculator import timeline
    from battle_attack_group_runtime import battle_attack_groups
    from world_coordinate_sampled_vital_native import observe as vital
    from world_coordinate_group_native import bind_groups
    from world_coordinate_mixed_native import observe as routed
    if not case.get('sampled_groups'):return vital(case)
    codes={timeline.CharState._fire.__code__,timeline.CharState._charge_fire.__code__}
    def inner(c):
        with battle_attack_groups(routing='native',coordinate_packets=True) as data:n,t=vital(c,shot_codes=codes)
        bind_groups(n,data);return n,t
    n,t=routed(case,observer=inner)
    n['landed_packets']=[dict(row,target='' if row['label']=='__enemy__' else row['label']) for row in n['landed_packets']]
    return n,t
