"""Static real-weapon normalization, without ticking a CPU battle.
This prepares mechanical input only; it does not enable roster GPU acceptance.
"""
from portable_runtime import UnsupportedPortable


def normalize_static_weapon(char,base_atk,enemy,*,camera=False):
    from calculator.timeline import CharState,in_optimal_range
    if type(camera) is not bool:raise ValueError('Camera ownership must be explicit')
    if type(char.get('weapon_mode_swap',False)) is not bool:raise UnsupportedPortable('Manual mode-swap flag must be boolean',reason='control',fields=['weapon_mode_swap'])
    state=CharState(char,base_atk,enemy.get('code'))
    weapon=state.weapon
    if state.fire_mode not in ('auto','auto_warmup','charge'):raise UnsupportedPortable('Unported real firing mode')
    stage=char.get('burst_stage') or state.burst_stage
    if str(stage) not in ('1','2','3','A'):raise UnsupportedPortable('Unported real burst stage')
    config=dict(base_weapon_type=state.base_weapon_type,enabled=True,mode=state.fire_mode,capacity=weapon['max_ammo'],coefficient=weapon['damage_coeff'],
                reload=weapon['reload_time'],raw_charge=weapon.get('charge_time') or 0,pellets=state.pellets,muzzles=state.muzzles,
                full_charge_mult=weapon.get('full_charge_mult',100),gauge=state.burst_energy,
                gauge_mult=weapon.get('full_charge_mult',100) if state.fire_mode=='charge' and camera else 100,
                stage=4 if str(stage)=='A' else int(stage),cooldown=weapon.get('burst_cooldown',40),
                optimal=bool(in_optimal_range(enemy,state.name,state.weapon_type,{})),
                element_match=bool(state.base_element_match),core_mult=weapon.get('core_dmg_mult',200),
                warmup=state.warmup_bullets,cooldown_time=state.mech.get('cooldown_time',1),
                spread_start=state.spread_start,spread_end=state.spread_end,spread_shots=state._spread_shots_needed,
                core_diameter=enemy.get('core_px',0),clip_count=state.clip_count,
                post_reload_delay=state.post_reload_delay,cover_during_delay=state.cover_during_delay,
                reload_cancel_on_full=state.reload_cancel_on_full)
    # Native keeps logical stage A for conditions, but default automatic Red
    # Hood selection is B3; explicit user stages and live overrides take priority.
    if char['name']=='레드 후드' and str(stage)=='A' and char.get('burst_stage') is None:config['automatic_burst_stage']=3
    if char.get('burst_stage') is not None:config['explicit_burst_stage']=True
    if state.fire_mode=='charge':
        config.update(charge=state.charge_time_base,interval=state.charge_time_base+state.post_fire_delay,min_cycle=state._min_fire_cycle)
    else:
        config.update(rate=state.fire_rate,interval=1/state.fire_rate,
                      rate_max=state.fire_rate_max if state.fire_mode=='auto_warmup' and state.fire_rate_max is not None else state.fire_rate)
    return config
