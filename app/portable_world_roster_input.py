"""Complete real preparation for the private shared world executor.

Only static native normalization is used: no battle, shot schedule, recipient
selection, computed damage or lifecycle is supplied by the CPU. Unsupported
policies/definitions fail closed; this adapter is not public certification.
"""
import copy
import struct

from portable_specs import LIMITS as L

SOURCE = 'gpu/world_roster_entry.slang'
INPUT_WORDS = L['WORLD_RELOAD_INPUT_WORDS']
OUTPUT_WORDS = L['WORLD_RELOAD_OUTPUT_WORDS']


def compile_world_battle(prepared, *, trace='burst', allow_physical_interrupt=False, coordinate=False):
    from portable_runtime import compile_program, UnsupportedPortable
    from calculator.timeline import DEFAULT_CONFIG, _resolve_cameras
    from calculator.boss_pattern import BossScript, DEFAULT_BOSS_ATK
    from portable_weapon_input import normalize_static_weapon
    from portable_geometry_specs import from_roster
    from portable_world_schedule_specs import compile_schedule
    from portable_world_attack_specs import pack_attacks
    from portable_world_overlay_specs import (
        compiler_effect, compile_payload, pack_cleanse_flags, pack_skill_mode_flags, CODES)
    from portable_actor_specs import compile_registry
    from portable_actor_pool_specs import compile_pools
    from portable_actor_state_specs import append_queries
    from portable_target_counter_program import compiler_effects, patch_program
    from portable_target_counter_specs import pack_battle
    from portable_charge_clock_specs import compile_clock, normalize_static_clock
    from portable_charge_control_specs import normalize_static_controls, compile_policy as controls_policy
    from portable_team_hit_specs import bound_effects, compile_policy as team_policy
    from portable_reload_specs import pack as pack_reload
    from portable_enemy_specs import damage_plan, enemy_buff_plan

    if prepared.get('cpu_battle_executed') is not False or prepared.get('all_character_effects_included') is not True:
        raise UnsupportedPortable('Complete static preparation without CPU battle execution required')
    if type(allow_physical_interrupt) is not bool:
        raise UnsupportedPortable('Physical interrupt opt-in must be a literal boolean')
    if type(coordinate) is not bool:raise UnsupportedPortable('Coordinate opt-in must be a literal boolean')
    chars = copy.deepcopy(prepared['chars'])
    names = [c['name'] for c in chars]
    if len(names) != 5 or len(set(names)) != 5:
        raise UnsupportedPortable('Five distinct real characters required')
    policies = prepared['policies']
    cfg = policies['config']
    allowed = {'duration', 'rng_mode', 'burst_gauge_mode', 'first_burst_time',
               'allow_unparsed', 'aim_interrupt', 'camera', 'camera_mode', 'control_mode'}
    if coordinate:allowed|={'burst_delay','burst_pattern','burst_sequence'}
    if prepared.get('_product_burst_patterns'):allowed|={'burst_pattern'}
    if set(cfg) - allowed or cfg.get('rng_mode') != 'expected' or cfg.get('burst_gauge_mode') != 'accumulate' or policies.get('expected') is not True:
        raise UnsupportedPortable('Real world requires expected RNG and accumulated burst gauge')
    if cfg.get('allow_unparsed') or (cfg.get('aim_interrupt') and not allow_physical_interrupt) or set(policies['auto']) != set(names):
        raise UnsupportedPortable('Unparsed effects, interrupt aiming or manual burst policy unconnected')
    if set(policies['controls']) != set(names) or any(policies['controls'][c['name']] != c.get('control', {}) for c in chars):
        raise UnsupportedPortable('Prepared control policy disagrees with real characters')
    enemy = copy.deepcopy(prepared['enemy'])
    if set(enemy) - {'def', 'code', 'core_px', 'has_parts', 'part_break_interval',
                     'optimal_range_weapons', 'distance', 'coord', 'atk', 'patterns'}:
        raise UnsupportedPortable('Unknown real enemy fields')
    if (enemy.get('coord') is not None and not coordinate) or enemy.get('part_break_interval', 0):
        raise UnsupportedPortable('Coordinate or implicit part-break scheduling unconnected')
    # Empty native world is represented by a single no-op root, not a CPU timeline.
    raw_patterns = enemy.get('patterns') or [dict(id='portable-empty-world', kind='idle')]
    literal_enemy=copy.deepcopy(enemy)
    if coordinate:
        from calculator.boss_pattern import coord_spec
        if coord_spec(enemy.get('coord')) is None:raise UnsupportedPortable('Explicit coordinate world required')
        raw_patterns=copy.deepcopy(raw_patterns)
        for p in raw_patterns:
            if p['kind']=='core':p.pop('x',None);p.pop('y',None)
            for target in p.get('targets',[]):
                for key in ('x','y','r','w','h','rotation','z'):target.pop(key,None)
                target['reach']=1
        enemy.pop('coord',None)
    duration = cfg['duration']
    graph, patterns = compile_schedule(dict(patterns=raw_patterns, clock='accumulated', duration=duration), notice_payload=True)
    BossScript(patterns, copy.deepcopy(enemy), lambda *_: False)
    registry, bindings = compile_registry(patterns, pools=True)
    cameras = _resolve_cameras(chars, {**DEFAULT_CONFIG, **cfg})
    camera_mask = sum(1 << i for i, n in enumerate(names) if n in cameras)
    attacks = prepared['base_atk']
    weapons = [normalize_static_weapon(c, attack, literal_enemy, camera=c['name'] in cameras)
               for c, attack in zip(chars, attacks)]
    if coordinate:
        from portable_manual_control_specs import normalize as normalize_controls
        control_chars=copy.deepcopy(chars)
        for c in control_chars:
            for axis in ('aim','cover','reload','burst'):c.get('control',{}).pop(axis,None)
        controls=normalize_controls(control_chars,attacks,literal_enemy,cfg.get('control_mode','solo'))
    elif prepared.get('_product_manual_cover'):
        from portable_manual_control_specs import normalize as normalize_controls
        control_chars=copy.deepcopy(chars)
        for c in control_chars:
            burst=c.get('control',{}).get('burst')
            if burst and (not prepared.get('_product_burst_patterns') or set(burst)-{'pattern'}):raise UnsupportedPortable('Manual product burst control requires its literal policy producer')
            c.get('control',{}).pop('burst',None)
        controls=normalize_controls(control_chars,attacks,enemy,cfg.get('control_mode','solo'))
    elif prepared.get('_product_burst_patterns'):
        control_chars=copy.deepcopy(chars)
        for c in control_chars:
            burst=c.get('control',{}).get('burst')
            if burst and set(burst)-{'pattern'}:raise UnsupportedPortable('Product burst delays/waits require their own literal policy producer')
            c.get('control',{}).pop('burst',None)
        controls=normalize_static_controls(control_chars,attacks,enemy,cfg.get('control_mode','solo'))
    else:controls = normalize_static_controls(chars, attacks, enemy, cfg.get('control_mode', 'solo'))
    delays = normalize_static_clock(chars, attacks, enemy)
    original = [(copy.deepcopy(x['effect']), x['owner']) for x in prepared['effects']]
    character_effects=len(original)
    boss_nodes={}
    if prepared.get('_product_boss_debuffs'):
        from portable_world_attack_specs import boss_debuff_effects
        effect_patterns=patterns
        if '_product_add_debuff_patterns' in prepared:
            from calculator.boss_pattern import validate
            effect_patterns=validate(copy.deepcopy(prepared['_product_add_debuff_patterns']),squad_size=5)
        boss_effects,boss_nodes=boss_debuff_effects(effect_patterns,names[0],enemy.get('atk',DEFAULT_BOSS_ATK))
        original.extend(boss_effects)
    lowered = [(compiler_effect(e), owner) for e, owner in original]
    compiled = list(zip(compiler_effects([e for e, _ in lowered]), [owner for _, owner in original]))
    target_spawn = any('event:target_spawn' in (*p.emit, *p.emit_end, *(e for x in p.targets for e in x.emits)) for p in patterns)
    script = [[duration,24,0,0,0,-1,0,0], [duration,30,0,0,0,-1,0,0],
              [duration,2,0,0,-1,0,0,0]]
    # Ordinary public query rows are compiled first; private finalizer40 follows.
    words, meta = compile_program(chars, compiled, script, attacks,
        native_equipment_carriers=prepared.get('_product_native_equipment_carriers',False),
        allies=prepared['allies'], cover_sync=bool(enemy.get('patterns')), native_landing=True,
        enemy_code=enemy.get('code'), geometry=from_roster(chars, enemy), world_frame=True,
        world_notice_names=('target_spawn',) if target_spawn else (),allied_seed=policies.get('seed'),native_snapshot_logging=True,focus_aim_layer2=cfg.get('aim_interrupt',False),
        combat=dict(weapons=weapons, targets=[dict(hp=1e30, defense=enemy['def'], attack=enemy.get('atk', DEFAULT_BOSS_ATK))],
                    trace=trace, clock='accumulated'))
    if len(words) != 86016:
        raise ValueError('World base wire dimensions changed')
    # The canonical counter view needs the overlay lowering but retains all identities.
    if any(e.get('target_counter') is not None or any(t.startswith('event:target_counter_complete:') for t in e.get('trigger', {}).get('timing', [])) for e, _ in original):
        patch_program(words, meta, chars, lowered)
    bound = bound_effects(original, meta, names)
    words.extend(graph)
    words.extend([0] * 512)
    words[L['ENEMY_TARGET_META_BASE']:L['ENEMY_TARGET_META_BASE']+8] = [1,0,0,0,0,0,0,0]
    meta['enemy_targeting'] = dict(enabled=True, steps=[], seed=0)
    if target_spawn:
        words[L['WORLD_FRAME_INPUT_BASE']+8] = meta['states']['target_spawn']+1
    if boss_nodes:
        from portable_world_attack_specs import pack_boss_debuffs
        pack_boss_debuffs(words,meta,character_effects,boss_nodes,L)
    pack_attacks(words, patterns, raw_patterns, L)
    tags = {p.code: meta['states'][p.code]+1 for p in patterns
            if p.kind == 'shield' and p.code in meta['states'] and words[L['WORLD_META_BASE']+1] != 0}
    words.extend(compile_payload(patterns, camera_mask=camera_mask,
        element_codes=[CODES.get(c['_weapon'].get('element_code', ''), 0) for c in chars] if any(p.kind == 'shield' for p in patterns) else (),
        code_tags=tags, named_refs={e['target_effect']:meta['states'][e['target_effect']]+1 for e,_ in original if e.get('stat')=='received_dmg_buff_mag_pct'}, charge_hold_mask=sum(1 << i for i,n in enumerate(names) if n == '스노우 화이트 : 헤비암즈'), actor_pools=True))
    pack_cleanse_flags(words, [e for e, _ in bound], L)
    pack_skill_mode_flags(words, [e for e, _ in bound], L)
    words.extend(registry)
    words.extend(compile_pools(patterns, bindings, fields=True, boss_atk=enemy.get('atk', DEFAULT_BOSS_ATK),focus_aim=bool(words[L['WORLD_META_BASE']+4]),armed=any(words[L['WEAPON_BASE']+i*L['WEAPON_WORDS']] and words[L['WEAPON_BASE']+i*L['WEAPON_WORDS']+1]==0 for i in range(5))))
    for i, (effect, _) in enumerate(bound):
        plan = enemy_buff_plan(effect)
        if plan is None and effect.get('type') == 'damage':
            plan = damage_plan(effect)
        if plan is not None and plan[0] == 2:
            words[L['DAMAGE_DEFINITION_BASE']+i*8+1] = 128
    words.extend([0] * (L['WORLD_ACTOR_STATE_INPUT_WORDS'] - len(words)))
    words[L['WORLD_ACTOR_POOL_INPUT_BASE']+4] = 0x57543031
    step = words[2]
    if step >= L['COMMANDS']:
        raise ValueError('Real world query capacity exceeded')
    words[L['COMMAND_BASE']+step*8:L['COMMAND_BASE']+(step+1)*8] = [40, *struct.unpack('<II', struct.pack('<d', duration)), 0,0,0,0,0]
    words[2] = step+1
    append_queries(words, meta, [], duration)
    from portable_target_counter_specs import pack_single_body_selectors
    pack_single_body_selectors(words,bound,bindings)
    words.extend(pack_battle([(e,names.index(owner)) for e,owner in bound], words[2], names, meta['states'], bindings, patterns, allow_no_counter=True))
    words.extend(compile_clock(weapons, delays))
    words.extend(team_policy(meta, enemy.get('has_parts', False)))
    if coordinate or prepared.get('_product_manual_cover'):
        from portable_manual_control_specs import pack as pack_controls
        policy=pack_controls(controls,bound,names,meta['states'],camera_mask)
        words.extend(policy);meta['_control_policy']=policy
    else:
        policy=controls_policy(controls,bound,names,meta['states'],camera_mask)
        words.extend(policy);meta['_control_policy']=policy
    words.extend(pack_reload((e for e,_ in bound),manual_swap=[c.get('weapon_mode_swap',False) for c in chars]))
    words[0] = 0x5045568c
    words[L['TARGET_COUNTER_INPUT_BASE']+6] = 23
    if len(words) != INPUT_WORDS:
        raise ValueError('Real world input dimensions changed')
    meta['real_prepared_input'] = dict(all_character_effects_included=True,
        prepared_effects=character_effects, bound_effects=len(bound), camera=sorted(cameras),
        cpu_battle_executed=False, full_catalog_certified=False,
        policy=copy.deepcopy(policies), actor_bindings=len(bindings))
    if allow_physical_interrupt:meta['real_prepared_input']['physical_interrupt_opt_in']=True
    if coordinate:meta['real_prepared_input']['coordinate_sidecar_required']=True
    if prepared.get('_product_native_equipment_carriers'):meta['real_prepared_input']['equipment_quantity_carriers']='native-named-state-v1'
    return words, meta
