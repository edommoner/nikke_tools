"""Conservative work routing for observed blockers, never feature admission."""


def reference_readiness(issue):
    result=dict(lane='reference_review',native_consumer='not_audited',contract_coverage='not_indexed',
        gpu_supported=False,gpu_admission_verified=False,full_character_verified=False,
        runtime_validation_performed=False)
    if issue.get('phase')=='effect' and issue.get('category')=='fields' and issue.get('kind')=='damage' and issue.get('stat')=='auto_damage' and issue.get('fields')==['weapon_type']:
        result.update(lane='reference_model_gap',native_consumer='actor_weapon_only',contract_coverage='recorded_subset',reference_suites=['skill-weapon','skill-weapon-rosters'],recorded_cases=16,reference_model_gap_cases=6,
            consumer_source='calculator/timeline.py:_handle_damage_eff; app/portable_skill_weapon_contract.py',
            note='The pinned native handler reads cs.weapon and base_weapon_type, not the effect annotation. Only a known declaration equal to the caster base weapon is admitted for normal_attack auto_damage. Effect-local override or mismatched annotation semantics remain unresolved; do not infer no-op support or in-game correctness')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='fields' and issue.get('kind')=='damage' and issue.get('stat') in ('sequential_damage:6','sequential_damage:13') and issue.get('target')=='enemies_random' and issue.get('fields')==['land_in_full_burst']:
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',contract_coverage='recorded_subset',recorded_cases=15,reference_suites=['full-burst-landing','full-burst-landing-rosters'],
            consumer_source='calculator/timeline.py:_handle_damage_eff,_handle_landing_damage,BurstController.tick; app/attack_timing_specs.py:full_burst_landing',
            required_extensions=['separate_latched_landing_mode_in_shared_pending_controller','retain_actual_landing_reference_read_before_latched_override','shared_cast_exclusion_and_normal_landing_packet_path','mixed_target_rng_and_numeric_basis_contracts','metal_and_current_source_cuda_validation'],
            note='Thirteen native fixtures and original Elegg Boom and Shock3/30s confirm cast-time gates/counts, landing-time buff queries, later-cast exclusions, same-frame full-burst landings and queued ordinary children. Cast reference1 is read as2 at landing before overriding back to1; preserve both calls. Original30s fires the6-hit branch;13-hit is synthetic only. GPU admission remains closed and no new GPU/full-character validation is claimed')
        return result
    operator=issue.get('operator')
    operator=operator if isinstance(operator,dict) else {}
    named_target=issue.get('target')
    if issue.get('phase')=='effect' and issue.get('category') in ('recipient','effect') and issue.get('kind')=='instant' and issue.get('stat')=='remove_named_buff' and isinstance(named_target,str) and named_target.startswith('enemies_with_buff:') and not issue.get('fields'):
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',contract_coverage='recorded_subset',recorded_cases=18,reference_suites=['named-enemy-removal','named-enemy-removal-rosters'],
            consumer_source='calculator/buff_manager.py:_dispatch_instant; gpu/world_actor_mutation.slang:actorMutationRemoveNamed',
            implemented_extensions=['target_scope_uses_shared_named_enemy_route','global_scope_does_not_consume_selector','existing_enemy_carrier_retirement_and_callbacks'],
            scoped_metal_validation=dict(suite='named-enemy-removal-retention',inputs=230,native_cases=171,rejected_cases=59,removal_contracts=16,original_profile_inputs=2,original_definitions=80,original_durations=[3,30],independently_audited=True),
            required_extensions=['periodic_timers_empty_removed_name_and_reentrant_callback_mixtures','broader_full_profiles_worlds_and_current_source_cuda_validation'],
            note='Sixteen native contracts cover48 dispatches and504 membership calls for target/global removal, opaque and empty selector names, fallback, self-marker removal, cross-caster and128 enemies. Original Asuka WILLE3/30s keeps all80 definitions; only30s dispatches removal. Private Metal scope is recorded separately from full-character/current-source CUDA certification')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='recipient' and isinstance(named_target,str) and named_target.startswith('enemies_with_buff:') and not issue.get('fields') and (issue.get('kind')=='buff' and issue.get('stat')=='received_dmg_pct' or issue.get('kind')=='instant' and issue.get('stat')=='named_buff_duration_extend' or issue.get('kind')=='damage' and (issue.get('stat')=='bonus_damage' or str(issue.get('stat','')).startswith('sequential_damage:'))):
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',contract_coverage='recorded_subset',recorded_cases=23,reference_suites=['named-enemy'],
            consumer_source='calculator/boss_pattern.py:_ranked,resolve_enemies,route; calculator/buff_manager.py:_resolve_enemies,enemy_has_state; calculator/timeline.py:_land',
            implemented_extensions=['opaque_name_operand_in_existing_mode_union','shared_actor_set_route','existing_named_presence_generation_and_query_scope','explicit_empty_name_tag'],
            scoped_metal_validation=dict(suite='named-enemy-retention',inputs=207,native_cases=155,rejected_cases=52,named_enemy_contracts=23,diagnostic_inputs=23,diagnostic_masks=69,independently_audited=True),
            required_extensions=['sequential_hit_references_scaling_budget_passive_contracts','broader_named_enemy_removal_mixtures','mixed_world_full_profiles_and_current_cuda_validation'],
            note='Twenty-three native contracts/628 actual membership calls fix body-first alive-add order, global caster-independent names, opaque colon/space/empty names, no-match boss fallback, expiry, retirement and reused-ID mark removal, across buffs/bonus damage/duration extension. Sequential/ref/scaling combinations need further contracts. Native observer classification is independent of portable admission for this prefix. Private shared Slang/Metal23 and retained207 now match native; diagnostic69 target masks agree. Public entries still reject this route; broader runtime/full-character/current-source CUDA certification remains incomplete')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='recipient' and issue.get('kind')=='instant' and issue.get('stat')=='debuff_cleanse' and issue.get('target') in tuple('allies_random_with_debuff:'+str(n) for n in range(6)) and not issue.get('fields') and issue.get('scaling') is None:
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',contract_coverage='recorded_subset',recorded_cases=38,reference_suites=['random-cleanse','random-cleanse-mixed','random-cleanse-budget','random-cleanse-rosters'],
            consumer_source='calculator/buff_manager.py:_resolve_target_raw,_has_harmful,_dispatch_instant',
            scoped_metal_validation=dict(suite='random-cleanse-retention',inputs=175,native_cases=132,rejected_cases=43,synthetic_contracts=36,original_profiles=1,original_definitions=71,original_durations=[3,30],zero_sample_initial_mt_verified=True,independently_audited=True,replay_gpu_calls=0),
            required_extensions=['periodic_and_broader_harmful_carrier_interactions','full_catalog_target_worlds','current_source_cuda_validation'],
            note='Thirty-six synthetic contracts plus complete Cocoa3/30s fix self inclusion, irremovable eligibility without removal, live expiry/down/revival, counts0..5 and ordered shared-carrier edits. Budget probes sample before dispatch; exhausted budgets sample zero times and empty pools spend no budget. Private shared Slang/Metal175 and independent seal passed; original owner-metadata comparison failure preserved, repaired by replay without another dispatch. Public entries retain rejection; broader interactions/full-character/current-source CUDA remain unverified')
        return result
    if issue.get('phase')=='gpu-admission' and issue.get('category')=='trigger' and operator.get('domain')=='condition' and operator.get('descriptor') in ('has_burst1_ally','no_burst1_ally'):
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',contract_coverage='recorded_subset',recorded_cases=12,reference_suites=['burst1-ally'],
            consumer_source='calculator/buff_manager.py:_condition_ok; gpu/event_runtime.slang:basicConditions',
            prior_rejecting_tier='gpu/world_actor_fields.slang:actorFieldsDefinitionValid',
            scoped_metal_validation=dict(suite='burst1-ally-retention',inputs=125,native_cases=94,rejected_cases=31,native_predicate_cases=12,predicate_checks=36,original_profiles=2,original_definitions=83,independently_audited=True),
            required_extensions=['other_caster_positions_and_broader_mixed_stage_contracts','current_source_cuda_validation','full_catalog_battle_validation'],
            note='Twelve native contracts fix caster exclusion, down allies, live stage overrides and expiry. The private actor-field admission uses the existing evaluator with zero-name/argument and combat guards. Metal125 and independent seal include both original Anis profiles; all95 previous raw outputs are unchanged. This recorded scope is not full-character or current-source CUDA certification; legacy entries retain rejection')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='fields' and issue.get('kind')=='buff' and issue.get('stat') in ('stealth','stun') and issue.get('target')=='self' and issue.get('fields')==['duration_scaling','duration_scaling_ref']:
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:_expires_at,ref_count,_apply',
            contract_coverage='recorded_subset',reference_suites=['duration-scaling','duration-scaling-mixed'],recorded_cases=40,
            real_original_definitions=80,real_durations=[3,30],
            implemented_extensions=['static_duration_reference_identity','activation_time_reference_before_carrier_mutation','source_definition_duration_for_named_alias','ordered_binary64_duration_expiry','passive_refresh','live_source_clock_and_precedence','raw_stack_operation_refresh_preserved'],
            scoped_metal_validation=dict(suite='duration-scaling',native_cases=40,rejected_cases=7,expiry_checks=160,reference_reads=154,independently_audited=True,diagnostic_replay_gpu_calls=0),
            required_extensions=['broader_type_and_state_combinations','current_source_cuda_validation','full_catalog_battle_validation'],
            note='Private shared Slang/Metal contracts27 synthetic, four full Label baseline/shield-break inputs and nine mixed consumers. Missing ref gives0; zero gauge/source shadows named stack; None/-1 skip ref reads; finite duration multiplies before time addition. Value scaling is independent, alias uses applying definition and refresh reads before own stack increment. Public entry still rejects; full-character and current-source CUDA certification remain unverified')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='trigger' and operator.get('domain')=='condition' and operator.get('descriptor')=='not_core':
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:_condition_ok,notify; calculator/timeline.py:_bullet_core_fracs,_fire,_charge_fire',
            contract_coverage='recorded_subset',reference_suites=['not-core'],recorded_cases=27,
            real_profiles=1,real_original_definitions=79,real_durations=[3,30],real_instant_handler_calls=[3,34],
            implemented_extensions=['native_optional_core_context_contract','native_independent_not_core_accumulator_contract','native_nested_notify_restore_contract','native_condition_and_budget_order_contract'],
            scoped_metal_validation=dict(suite='not-core',native_cases=27,rejected_cases=5,private_entry='gpu/world_not_core_entry.slang',independently_audited=True),
            required_extensions=['broader_mixed_passive_numeric_context_consumers','current_source_cuda_validation','full_catalog_battle_validation'],
            note='Expected-mode contracts25 plus complete Winter Guillotine3/30s verified on the private Metal entry. Physical hit_count freezes core_frac; absent context means non-core, including last_bullet. Definition/caster accumulators are separate from probability, preserve ordered duplicate conditions and evaluate before activation budget. The tested passive subset has no core context. Public/legacy entry still rejects; broader mixed consumers and current-source CUDA are unverified')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='trigger' and operator.get('domain')=='timing':
        import re
        if re.fullmatch(r'non_full_charge_fire_count:[1-9][0-9]*',str(operator.get('descriptor',''))):
            result.update(lane='native_contract_extension',native_consumer='confirmed_source',
                consumer_source='research/upstream/nikke-calc-master/calculator/timeline.py:_charge_fire,_tap_timing,_tick_charge; calculator/buff_manager.py:_timing_to_index_key,_timing_match',
                contract_coverage='recorded_subset',reference_suites=['nonfull-charge','nonfull-charge-reduction','partial-query'],recorded_cases=47,
                implemented_extensions=['partial_and_full_notice_partition','caster_owned_counter','duplicate_and_raw_alias_multiplicity','trigger_reduction_and_budget','tap_full_override','per_shot_not_per_muzzle_counter','partial_charge_weapon_state_and_tap_controls','damage_core_and_burst_gain_snapshots','signed_base_subtract_before_clamp','tap_numeric_query_timing_and_rng','live_heal_multiplier_reads','mode_exit_numeric_invalidation'],
                scoped_gpu_suite='partial-query-retention',scoped_metal_cases=65,scoped_metal_rejections=26,scoped_metal_validation_performed=True,
                real_gpu_suite='partial-charge-rosters',real_profiles=1,real_original_definitions=77,real_max_duration=30,
                required_extensions=['broader_numeric_stats_and_control_interleavings','full_catalog_partial_charge_rosters','current_source_cuda_validation'],
                note='Private partial-charge entry matches65 native inputs and26 raw rejections inside1533 retained Metal inputs. Seventeen mixed query contracts preserve complete random order/final MT across tap/full/auto, live healing and mode exit. Includes all77 Crust definitions at3/30s with automatic/tap controls; bounded physical trace retains omissions. Static packing is not GPU admission or full-character certification. Public entry still rejects event40/tap wire2. Additional consumers, catalog and current-source CUDA remain unverified')
            return result
    if issue.get('phase')=='effect' and issue.get('kind')=='buff' and issue.get('stat') in ('atk_caster_based_pct','atk_from_hp_pct'):
        import re
        if re.fullmatch(r'allies_random:[1-5]',str(issue.get('target',''))):
            result.update(lane='native_contract_extension',native_consumer='confirmed_source',
                consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:get_buffs,_resolve_target,_resolve_lazy',
                contract_coverage='recorded_subset',reference_suites=['late-attack-random'],recorded_cases=11,
                required_extensions=['additional_stat_query_consumers','mixed_revive_and_random_sequences','current_source_cuda_validation'],
                implemented_extensions=['late_attack_direct_recipient_reads','bounded_random_history','dictionary_query_cache_boundaries','real_roster_rng_consumption','native_logging_and_hp_sync'],
                scoped_gpu_suite='ordered-history-battles',scoped_metal_cases=17,scoped_metal_validation_performed=True,
                resolved_gpu_mismatch_suite='state-focus-rosters',
                note='Eleven authored contracts and six original full-roster inputs match on Metal, including all4550 Lily30s selections, logging and HP-sync consumers. Continue broader stat-consumer and mixed-state coverage; current-source CUDA remains unverified. Broken-cover recipients are eager, ordinary random late readers remain direct. Preserve failures; this is not a missing CPU model or full-character support')
            return result
    if issue.get('phase')=='program' and issue.get('category')=='control' and issue.get('fields')==['focus_aim_physical_interrupt']:
        result.update(lane='reference_review',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/timeline.py:_land_target; app/impact_runtime.py:landing; app/world_actor_runtime.py:ActorRegistry.view',
            contract_coverage='recorded_subset',reference_suites=['interrupt-aim','aimed-packets','aimed-area','aimed-callback','aimed-enemy','aimed-rosters'],recorded_cases=82,
            implemented_extensions=['private_native_interrupt_receipts','zero_canonical_credit_contract','same_frame_dead_accounting','respawn_generation_contract','charge_and_lifesteal_contracts','shared_private_interrupt_landing_bridge','scoped_metal_full_battle_and_receipts','aimed_no_core_intercept_factors','native_multipacket_shot_observer','aimed_pierce_explosion_packet_set','aimed_target_exclusion_and_frozen_factors','scoped_aimed_counter_children_and_lifesteal','canonical_enemy_scope_for_aimed_interrupt','scoped_full_profile_target_worlds'],
            scoped_gpu_suite='aimed-area-retention',scoped_metal_cases=12,scoped_metal_receipts=74,prior_direct_metal_cases=24,scoped_metal_validation_performed=True,
            callback_gpu_suite='aimed-callback',callback_metal_cases=20,callback_private_receipts=184,
            real_gpu_suite='aimed-rosters',real_metal_cases=12,real_profiles=3,real_max_duration=30,real_private_receipts_individually_traced=False,
            required_extensions=['full_catalog_target_worlds_and_broader_callbacks','current_source_cuda_validation'],
            note='Scoped Metal area12/private74 receipts and callback20/private184 receipts use the shared landing engine. Six logical enemy contracts keep physical interrupt identity separate from body scope for fields, named removal and boss/add predicates. Three complete base profiles in2 worlds at3/30s give12 real Metal cases; compare battle state/gates/burst, bounded physical history with counted omissions, all pool/accounting rows and ordered RNG. Native packet contracts do not imply individual GPU tracing of every packet. Catalog/variants and broader callbacks remain unverified; current-source CUDA unverified. Development-only, default public/typed CPU entry unchanged, no full-character promotion')
        return result
    if issue.get('phase')=='effect' and issue.get('kind')=='buff' and issue.get('category')=='trigger' and operator.get('domain')=='condition' and operator.get('descriptor') in ('no_broken_cover_ally','focusing'):
        focus=operator['descriptor']=='focusing'
        reader_pending=focus and issue.get('stat') not in ('atk_pct','focus_fire')
        result.update(lane='native_contract_extension' if reader_pending else 'reference_review',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:_condition_ok,_runtime_condition_ok,cover_alive,_alive,get_buffs',
            contract_coverage='recorded_subset',reference_suites=['state-predicates']+(['focus-aim'] if focus else []),recorded_cases=15,
            scoped_gpu_suite='state-focus',scoped_metal_validation_performed=True,
            required_extensions=['numeric_query_reader_cache_contract'] if reader_pending else [],
            note='Shared cover/camera predicates and focus presence/aim are connected in scoped Metal cases. Numeric dictionary camera eligibility differs from selective live reads; audit the remaining stat consumers/cache invalidations before broad promotion. Full character support remains unverified')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='recipient' and issue.get('kind') in ('buff','instant'):
        import re
        if re.fullmatch(r'allies_(?:broken_cover_)?random:[1-5]',str(issue.get('target',''))):
            result.update(lane='reference_review',native_consumer='confirmed_source',
                consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:_resolve_target_raw,_resolve_lazy',
                contract_coverage='recorded_subset',reference_suites=['ally-random'],recorded_cases=18,scoped_metal_cases=20,
                scoped_gpu_suite='ally-random-gpu',scoped_metal_validation_performed=True,
                required_extensions=[],
                note='Connected shared allied RNG and lazy/eager recipients; scoped Metal20 contracts only. An old recipient diagnostic now needs context review; mixed revival/random, ordered random buff lists and full characters remain unverified')
            return result
    if issue.get('phase')=='program' and issue.get('category')=='control' and issue.get('fields')==['weapon_mode_swap']:
        result.update(lane='reference_review',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/timeline.py:CharState.tick; calculator/buff_manager.py:manual_swap_ready',
            contract_coverage='recorded_subset',reference_suites=['manual-swap','manual-swap-rosters'],recorded_cases=26,
            note='Known mode-swap subset has a separate shared Metal proof; this issue alone does not identify an unported valid control. Review malformed input or combined policies without inferring admission')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='trigger' and issue.get('kind')=='buff' and issue.get('target')=='self' and issue.get('operator')==dict(domain='condition',descriptor='self_undying'):
        result.update(lane='reference_review',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:_condition_ok,has_live_stat,_live',
            contract_coverage='recorded_subset',reference_suites=['undying-predicate','undying-predicate-rosters'],recorded_cases=25,
            note='Known explicit-activation subset has separate shared Metal proof with22 authored and3 whole Makima inputs. Review passive/context/malformed issues; this diagnostic alone does not identify an unported valid predicate')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='trigger' and issue.get('kind')=='buff' and issue.get('target')=='self' and issue.get('operator')==dict(domain='condition',descriptor='self_stat_above:accuracy_pct:0'):
        result.update(lane='reference_review',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:_condition_ok',
            contract_coverage='recorded_subset',reference_suites=['accuracy-predicate','accuracy-predicate-rosters'],recorded_cases=28,
            note='Known activation stat-query subset has separate shared Metal proof with26 authored and2 whole profiles. Review the current context/malformed issue without inferring full admission')
        return result
    if issue.get('phase')=='effect' and issue.get('kind')=='damage' and issue.get('fields')==['hits_parts']:
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/timeline.py:_coord_skill_hits,_handle_damage_eff,_reach_hit',
            contract_coverage='recorded_subset',reference_suites=['parts-skill','parts-skill-extended','parts-skill-lifecycle'],recorded_cases=32,reference_model_gap_cases=1,
            note='Non-coordinate packet/accounting contracts only; legacy deferred bonus drops part metadata and named-hit notify. No GPU admission; coordinate/interrupt world adapters remain separate constraints')
        return result
    if issue.get('phase')=='effect' and issue.get('kind')=='instant' and issue.get('stat')=='squad_ammo_consume_as':
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:_dispatch_instant',
            contract_coverage='recorded_subset',reference_suites=['ammo-equivalent'],recorded_cases=25,
            note='Literal caster quantity, finite bounded lowering domain; native truncation/extra notices/recursion/tick contracts only, not GPU admission or full-profile certification')
        if issue.get('category')=='effect' and not issue.get('fields') and issue.get('scaling') is None and issue.get('target')=='self':
            result['lane']='gpu_lowering_candidate'
        return result
    if issue.get('phase')!='effect' or issue.get('kind')!='buff':return result
    stat=issue.get('stat')
    if stat=='received_dmg_split':
        result.update(lane='reference_model_gap',native_consumer='specification_deferred_in_pinned_source',
            consumer_source='research/upstream/nikke-calc-master/docs/IMPL-STATUS.md:received_dmg_split',
            note='Differential allocation ratios are undefined in the pinned specification; self_cover and actor delivery are both deferred. Do not alias to received_dmg_split_even or accept as no-op')
    elif stat=='heal_split':
        result.update(native_consumer='declared_cpu_model',consumer_source='app/heal_sharing_compat.py',
            contract_coverage='recorded_subset',reference_suites=['heal-share','heal-share-extended','heal-share-targets','heal-share-lifesteal'],recorded_cases=43,
            lane='native_contract_extension',note='Declared model choices still need in-game confirmation; contracts are not exhaustive')
        if issue.get('category')=='effect' and not issue.get('fields') and issue.get('scaling') is None and issue.get('target') in ('self','all_allies'):
            result['lane']='gpu_lowering_candidate'
    elif stat in ('projectile_dmg_pct','shield_dmg_pct'):
        result.update(lane='native_consumer_research',native_consumer='unconfirmed',
            note='No confirmed consumer in this audit; unchanged output alone does not prove absent semantics')
    elif stat=='cover_def_pct':
        from effect_spec import SCOPED_INERT
        if stat in SCOPED_INERT:
            result.update(lane='reference_model_gap',native_consumer='scoped_inert_in_current_model',
                consumer_source='app/effect_spec.py:SCOPED_INERT',note='Clarify incoming-cover semantics before GPU lowering')
    return result


def work_lanes(priorities):
    """Indexes into the unchanged frequency ranking; no predicted unlock counts."""
    lanes={name:[] for name in ('gpu_lowering_candidate','native_contract_extension','native_consumer_research','reference_model_gap','reference_review')}
    for index,row in enumerate(priorities):lanes[row['reference_readiness']['lane']].append(index)
    return lanes
