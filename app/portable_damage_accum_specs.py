"""Static damage-pool policies. Runtime quantities are always GPU-owned."""
KINDS={'dmg_accum_dealt_atk_pct':13,'dmg_accum_received_atk_pct':14,'dmg_accum_rate_pct':15,'accum_split_damage':16}
HEADER_BASE=260666
QUEUE_BASE=260668
QUEUE_COUNT=512

def validate(effect,*,combat,world_frame):
    kind=KINDS.get(effect.get('stat'),0)
    if not kind:return False
    if combat is None or not world_frame:raise ValueError('Damage accumulation requires a private combat world')
    if effect.get('type')!=('damage' if kind==16 else 'buff'):raise ValueError('Wrong damage-accumulation effect kind')
    if effect.get('tick_interval') or effect.get('tick_start'):raise ValueError('Periodic damage-accumulation carriers are not connected')
    if effect.get('scaling') not in ((None,'lost_hp_pct') if kind==15 else (None,)):raise ValueError('Unported damage-accumulation scaling')
    if kind==16 or kind==15 and effect.get('target_effect') is not None:
        if not isinstance(effect.get('target_effect'),str) or not effect['target_effect']:raise ValueError('Damage accumulation requires a nonempty target_effect')
    if effect.get('duration_bullets',-1)!=-1:raise ValueError('Damage accumulation bullet lifetime is not connected')
    return True

def policy(effect):
    kind=KINDS.get(effect.get('stat'),0)
    if not kind:return 0
    return kind | (256 if kind==15 and effect.get('target_effect') is not None else 0) | (512 if kind==15 and ('fixed_value' in effect or 'values' in effect) else 0) | (1024 if kind in (13,14) and effect.get('name') else 0)

def compiler_effect(effect):
    # The legacy compiler refuses duplicate accumulator names. Private runtime
    # instance semantics are explicit and independently tested; preserve names,
    # authored values/targets, and restore the canonical stat IDs in wire data.
    return dict(effect,stat='') if effect.get('type')=='buff' and effect.get('stat') in ('dmg_accum_dealt_atk_pct','dmg_accum_received_atk_pct') else effect

def audit_layout(limits):
    """Reuse the ownership auditor without changing any prior mode/capacity."""
    from portable_scratch_layout import Bank,banks,verify
    reserved=[Bank('damage-accum-header',HEADER_BASE,2),Bank('damage-accum-notice-scratch',QUEUE_BASE,QUEUE_COUNT*2)]
    modes=[]
    for mode in ('normal','native-query-diagnostic','heal-share-diagnostic','interrupt-aim-diagnostic','heal-charge'):
        verify(limits,mode=mode)
        owners=banks(limits,mode)
        for i,new in enumerate(reserved):
            assert 0<=new.base<new.end<=limits['WORLD_RELOAD_OUTPUT_WORDS']
            for other in owners+reserved[:i]:assert new.end<=other.base or other.end<=new.base,(mode,new,other)
        modes.append(mode)
    return dict(verified=True,modes=modes,header=[HEADER_BASE,HEADER_BASE+2],queue=[QUEUE_BASE,QUEUE_BASE+QUEUE_COUNT*2],gpu_calls=0)
