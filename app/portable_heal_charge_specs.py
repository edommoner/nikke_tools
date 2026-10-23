"""Typed received-healing pool, live capacity modifier and named discharge."""
KINDS={'heal_overcharge_store_atk_pct':10,'accumulate_max_scale_pct':11,'heal_overcharge_discharge':12}
TRACE_BASE=771072
TRACE_COUNT=512
TRACE_WORDS=20
TRACE_MAGIC=0x48434731

def validate(effect,*,combat,world_frame):
    kind=KINDS.get(effect.get('stat'),0)
    if not kind:return False
    if combat is None or not world_frame:raise ValueError('Received-healing charge requires a private combat world')
    if effect.get('type')!=('instant' if kind==12 else 'buff'):raise ValueError('Wrong received-healing charge effect kind')
    if effect.get('tick_interval') or effect.get('scaling') not in (None,'stack_count'):raise ValueError('Unported periodic or scaled healing charge')
    if kind==12 and effect.get('scaling') is not None:raise ValueError('Discharge uses the stored amount')
    if kind==12 or kind==11 and 'target_effect' in effect:
        if not isinstance(effect.get('target_effect'),str) or not effect['target_effect']:raise ValueError('Healing charge requires a nonempty named target_effect')
    return True
