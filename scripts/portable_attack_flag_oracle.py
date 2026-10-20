"""Independent native BuffManager/CharState flags and declared skill families."""


def observe(case):
    if case.get('attack_flag_skill_reference'):
        from portable_enemy_oracle import observe as enemy
        return dict(queries=enemy(case)['queries'])
    from portable_weapon_oracle import observe as physical
    queries,state=physical(case)
    return dict(queries=queries,weapons=[state])


def compare(case,gpu,contains):
    native=observe(case)
    contains(native['queries'],case['expected_queries'],case['name']+'.authored_native')
    contains(gpu,native,case['name']+'.native_attack_flag')
    return native
