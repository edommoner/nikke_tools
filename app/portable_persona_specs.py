"""Native presence marker and canonical innate-B3 persona recipient selector."""
FLAG=1
SELECTOR=18


def validate(effect,*,combat,world_frame):
    marker=effect.get('stat')=='persona_state'
    selector=effect.get('target')=='allies_burst3_persona_excl_self'
    if not marker and not selector:return
    if combat is None or not world_frame:raise ValueError('Persona requires private combat-owned state')
    if marker:
        from portable_enemy_specs import enemy_buff_plan
        if effect.get('type')!='buff' or enemy_buff_plan(effect) is not None:
            raise ValueError('Persona marker requires an allied buff')
