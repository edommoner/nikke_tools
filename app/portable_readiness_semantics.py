"""Conservative work routing for observed blockers, never feature admission."""


def movement_contract():
    return dict(suite='enemy-movement-common',cases=5,source='app/enemy_movement_model.py',
        original_profiles=['유니','얀'],original_profile_definitions=[69,71],combined_original_roster=True,
        existing_duration_carriers=True,existing_actor_generations=True,existing_ADD_colliders=True,
        existing_shot_landing_damage=True,half_open_expiry_splitting=True,
        recipient_policy='canonical-all-in-range',force_policy='snap-to-declared-center',
        simultaneous_precedence='explicit; no game default',
        math_suite='enemy-movement-math',gpu_world_consumer_connected=True,
        declared_battle_validation=dict(suite='enemy-movement',inputs=15,native_cases=5,rejected_cases=10,
            metal_verified=True,independently_audited=True,cuda_verified=False,
            evidence='tests/fixtures/enemy-movement-battle-metal-v1.json',
            evidence_sha256='e05cf6ce26fabbea4bf80a4715398ee5963fb831ea72f6ed5fa052c04b22fb88',
            scope='Five full original 30-second battles with declared ADD motion and canonical all-in-range approximation; no game/default certification'),
        declared_math_validation=dict(inputs=43,native_cases=34,rejected_cases=9,overflow_status_witnesses=2,
            metal_verified=True,independently_audited=True,gpu_world_consumer_connected=False,cuda_verified=True,
            cuda_evidence='tests/fixtures/enemy-movement-math-cuda-v1.json',
            cuda_evidence_sha256='8b429466e38d1768a7b9305c886d9219ed227c6bf30872ffc2a6090d3202ce17',
            cuda_scope='43 step arithmetic inputs only; source-host CUDA audit plus fresh Mac word comparison; no CUDA battle certification',
            evidence='tests/fixtures/enemy-movement-math-metal-v1.json',
            evidence_sha256='61308665f6880894e4f5f0de2b7d19fc665ab7f80c02c9a17252d3fc12752a4b',
            scope='Ordered step arithmetic and explicit precedence only; no GPU carrier/actor/frame integration'),
        declared_typed_composition=dict(suite='moving-typed',inputs=18,native_cases=6,rejected_cases=12,
            metal_verified=True,independently_audited=True,cuda_verified=False,
            shared_canonical_pellet=True,existing_actor_generations=True,precomputed_positions=False,
            attachment_policy='visible-with-moving-owner-v1',
            evidence='tests/fixtures/moving-typed-metal-v1.json',
            evidence_sha256='d7bd92a83c82d7c49463f556fdaf756f8330a39d8158e70dfa1f0e3a54cc9d3b',
            default_producer_installed=False,in_game_attachment_policy_verified=False,
            scope='Six full original 30-second battles; movement frames/intervals and existing physical/battle comparison; explicit attachment model only'),
        declared_group_composition=dict(suite='moving-group',inputs=15,native_cases=3,rejected_cases=12,
            metal_verified=True,independently_audited=True,cuda_verified=False,
            original_definitions_per_roster=71,actual_group_consumer=True,
            evidence='tests/fixtures/moving-group-metal-v1.json',
            evidence_sha256='49ab674e94b3331ed23809a691f1919e41247516fb87924d28e0bbc278a8e02a',
            default_producer_installed=False,in_game_motion_policy_verified=False,
            scope='Original Yuni/Nihilister 30-second moving/typed battles, outside control and respawn; no game/default/all-character certification'),
        declared_maximum_slots=dict(suite='moving-many',inputs=13,native_cases=1,rejected_cases=12,
            metal_verified=True,independently_audited=True,cuda_verified=False,
            add_slots=127,duration=30,frames=228727,segments=228854,history_capacity=262144,
            evidence='tests/fixtures/moving-many-metal-v1.json',
            evidence_sha256='19b5b4b2a5226fa567a46cda3d6f05023f90658d56c9e85890a54b797b8046cf',
            default_producer_installed=False,in_game_motion_policy_verified=False,
            scope='One original 71-definition battle at full 127 ADD slots; two near colliders and 125 far, not all simultaneous hits or all-character certification'),
        current_cuda_verified=False,default_producer_installed=False,
        actual_spatial_recipient_selection_verified=False,in_game_motion_policy_verified=False,
        scope='Declared CPU and Metal movement consumer on real ADD colliders; canonical/default world model and actual game spatial rules remain unverified')


def current_movement_overlap_validation():
    return dict(suite='moving-overlap',inputs=14,native_cases=2,rejected_cases=12,
        original_definitions_per_roster=72,validated_original_operators=['enemy_movement_disable','force_move'],
        original_group_consumer=True,metal_verified=True,independently_audited=True,cuda_verified=False,
        evidence='tests/fixtures/moving-overlap-metal-v1.json',
        evidence_sha256='b86c759ebcce5efac7ab8637c8fa2b23d4d448172c10d896a4e0f43a31dd61ec',
        default_producer_installed=False,in_game_motion_policy_verified=False,in_game_precedence_verified=False,
        full_character_verified=False,
        scope='Current-source original Yuni/Yan/Nihilister shared typed/group battle; two explicit precedence models, no game/default/all-character certification')


def current_movement_stop_validation():
    return dict(suite='moving-group-current',inputs=15,native_cases=3,rejected_cases=12,
        metal_verified=True,independently_audited=True,current_source_recertified=True,cuda_verified=False,
        validated_original_operators=['enemy_movement_disable'],force_move_original_profile_revalidated=False,
        evidence='tests/fixtures/moving-group-current-metal-v2.json',
        evidence_sha256='a5c2307da2ce673208af4b8b6602c014b3d37ae086cc0ab70732d5cb1be1cca5',
        default_producer_installed=False,in_game_motion_policy_verified=False,full_character_verified=False,
        scope='Current-source original Yuni/Nihilister group battles only; no current Yan force-move, CUDA, game or default certification')


def enemy_ammo_prerequisites():
    """Existing numeric operator and the missing enemy state/producer boundary."""
    return dict(native_operator='calculator/timeline.py:handle_ammo_charge_pct',
        shared_numeric_operator='gpu/ammo_instant_runtime.slang:applyAmmoInstant',
        arithmetic_order='round(max_ammo * (value / 100)); clamp(current + change, 0, max_ammo)',
        rounding='binary64 division then multiplication; ties-to-even integer round',
        named_completion='For a nonempty effect name, native handler notifies once after its recipient loop, including an empty loop',
        required_state=['actor generation and liveness','weapon/mode and capacity modifiers','effective magazine capacity','remaining ammunition','reload deadline and full-magazine cancellation'],
        required_producers=['enemy shot consumption','enemy reload completion','original instant event and completion order'],
        enemy_state_defined=False,enemy_instant_connected=False,
        enemy_shot_reload_connected=False,original_profile_gpu_verified=False,
        current_cuda_verified=False,default_producer_installed=False,
        declared_enemy_ammo_self_destruct_validation=dict(suite='enemy-ammo-self-destruct',inputs=16,native_cases=8,
            source='gpu/world_enemy_ammo_self_destruct_entry.slang',original_profile='벨벳',original_definitions=76,
            evidence='tests/fixtures/enemy-ammo-self-destruct-independent-v1.json',
            evidence_sha256='5968e9d2adb198c8df57704128c8721513907fa6c9811efdb824b4f4d5773a03',
            metal_verified=True,independently_audited=True,ammo_connected=True,
            final_queued_hits_survive_retirement=True,original_incoming_executor_reused=True,
            fixed_magazine_and_reload=True,retirement_uses_original_scheduled_attempts=True,
            output_ownership_disjoint=True,cuda_verified=False,default_producer_installed=False),
        declared_enemy_ammo_self_destruct_contract=dict(suite='enemy-ammo-self-destruct-common',cases=8,
            source='app/enemy_ammo_self_destruct_model.py',original_profile='벨벳',original_definitions=76,
            capacity_model='fixed-declared',canonical_retirement_queue_observed=True,
            retired_delivery_scope='Exact queued hit object, same actor generation and same native frame only',
            schedule_retirement_unchanged_when_ammo_blocked=True,
            gpu_wire_connected=False,metal_verified=False,cuda_verified=False,default_path_installed=False),
        declared_add_self_destruct_validation=dict(suite='add-self-destruct',inputs=14,native_cases=8,
            source='gpu/world_add_self_destruct_entry.slang',original_definition_counts=[70,76],
            evidence='tests/fixtures/add-self-destruct-independent-v1.json',
            evidence_sha256='4d6368090649cf91ab1bf235e8181cf6dedd6a30bd423dfb476e6a921659e690',
            metal_verified=True,independently_audited=True,original_incoming_executor_reused=True,
            final_queued_hits_survive_retirement=True,death_resource_callbacks_verified=True,
            same_frame_death_and_count_update=True,until_cleared_renewal_verified=True,
            ammo_connected=False,cuda_verified=False,default_producer_installed=False),
        declared_add_self_destruct_contract=dict(suite='add-self-destruct-native',cases=4,
            source='research/world_add_self_destruct_native.py',
            evidence='research/target-count-query-evidence/add-self-destruct-native-contract-v1.json',
            canonical_component_verified=True,final_queued_hits_survive_retirement=True,
            same_frame_death_and_count_update=True,full_battle_verified=False,
            gpu_wire_connected=False,metal_verified=False,cuda_verified=False,
            default_producer_installed=False),
        declared_enemy_ammo_validation=dict(suite='enemy-ammo',inputs=20,native_cases=6,
            source='gpu/world_enemy_ammo_entry.slang',original_profile='벨벳',original_definitions=76,
            evidence='tests/fixtures/enemy-ammo-independent-v1.json',
            evidence_sha256='700d69a84b4cbc6fa27b5c61547bf091f3a671f3c044ab79d045bc654abb4427',
            metal_verified=True,independently_audited=True,actual_actor_pool_connected=True,
            original_incoming_executor_reused=True,ammo_connected=True,
            capacity_model='fixed-declared',resource_notification_capacity=4096,
            enemy_weapon_changes=False,capacity_modifiers=False,cuda_verified=False,
            default_producer_installed=False),
        declared_add_battle_validation=dict(suite='add-attack-battle',inputs=17,native_cases=6,
            source='gpu/world_add_attack_battle_entry.slang',original_profile='니힐리스타',original_definitions=70,
            evidence='tests/fixtures/add-attack-battle-independent-v2.json',
            evidence_sha256='ed2e3457673ca0ff610b049f8521f84c566b8f3783931f98b8025bfba9839f28',
            metal_verified=True,independently_audited=True,actual_actor_pool_connected=True,
            original_incoming_executor_reused=True,ammo_connected=False,cuda_verified=False,
            default_producer_installed=False),
        declared_add_firing_component=dict(suite='add-attack-schedule',inputs=19,native_cases=8,
            source='gpu/world_add_attack_cursor.slang',metal_verified=True,independently_audited=True,
            evidence='tests/fixtures/add-attack-schedule-independent-v1.json',
            evidence_sha256='51fe8079f089525c3b17cf14f1e778967658292cef38d0b0deacf102d01d6036',
            shared_graph_clock=True,queued_attacks=187,authored_clear_stimuli=True,
            full_battle_actor_pool_connected=False,ammo_connected=False,cuda_verified=False,
            self_destruct_supported=False,default_producer_installed=False),
        declared_cpu_contract=dict(suite='enemy-ammo-common',cases=6,
            source='app/enemy_ammo_model.py',original_profile='벨벳',original_definitions=76,
            capacity_model='fixed-declared',original_operator_code_reused=True,
            original_frame_and_attack_producers=True,original_scheduled_attempts_retained=True,
            generation_owned_remaining_and_reload=True,
            unsupported=['enemy weapon changes','capacity modifiers','flat ammo and forced reload','self-destruct launch timing'],
            gpu_wire_connected=False,metal_verified=False,cuda_verified=False,default_path_installed=False,
            scope='Opt-in CPU contract location; inspect the reference report for execution evidence, not canonical enemy state'))


def reference_readiness(issue):
    result=dict(lane='reference_review',native_consumer='not_audited',contract_coverage='not_indexed',
        gpu_supported=False,gpu_admission_verified=False,full_character_verified=False,
        runtime_validation_performed=False)
    operator=issue.get('operator') or {}
    if not isinstance(operator,dict):operator={}
    missing_stats=('enemy_movement_disable','force_move','effect_range_pct','effect_target_count_add','lock_on')
    missing_target=(issue.get('kind')=='damage' and issue.get('target') in ('all_projectiles','target_and_nearby:2'))
    missing_enemy_quantity=(issue.get('target')=='all_enemies' and (issue.get('kind'),issue.get('stat')) in (('buff','heal_received_pct'),('instant','ammo_charge_pct')))
    typed_foundation=dict(suite='destructible-counter',inputs=18,native_cases=13,rejected_cases=5,independently_audited=True,
        scope='declared_typed_world_resolved_landings_and_existing_counter_children_only',
        metal_verified=True,cuda_device_verified=False,battle_producers_verified=False,damage_factors_verified=False)
    modifier_battle=dict(suite='destructible-modifier-battle',inputs=18,native_cases=12,rejected_cases=6,metal_verified=True,independently_audited=True,actual_scheduler_verified=True,same_frame_stack=True,parent_damage_frozen=True,named_coefficient_observed=True,physical_body_factor_unchanged=True,projectile_target_only=True,hp_shield_battle_verified=False,cuda_device_verified=False,in_game_rules_verified=False,original_full_profile_verified=False,scope='opt_in_plain_projectile_skill_with_declared_modifier_model')
    if issue.get('phase')=='effect' and not issue.get('fields') and issue.get('scaling') is None and (issue.get('kind')=='buff' and issue.get('stat') in missing_stats or missing_target or missing_enemy_quantity):
        result.update(lane='reference_model_gap',native_consumer='missing_canonical_world_or_quantity_consumer',consumer_source='app/portable_model_gap_audit.py; app/portable_missing_consumer_audit.py; calculator/boss_pattern.py:_ranked; calculator/timeline.py:_register_instant_handlers',
            required_extensions=['explicit_world_or_quantity_model','typed_target_lifecycle_and_producer_contracts','shared_execution_and_current_CUDA_Metal_battle_validation'],
            note='Pinned source leaves movement/lock/range/target-count unimplemented. target_and_nearby falls back to one aimed target without a nearby spatial model; all_projectiles returns before damage. Enemy ammunition is filtered out by the allied instant handler, though its named completion still emits. Pinned default enemy healing has no verified recipient path. Keep these effects rejected; source audits and typed-state core do not certify battle support')
        if issue.get('kind')=='instant' and issue.get('stat')=='ammo_charge_pct' and issue.get('target')=='all_enemies':
            result['enemy_ammo_prerequisites']=enemy_ammo_prerequisites()
        if issue.get('stat') in ('enemy_movement_disable','force_move'):
            result['movement_prerequisites']=dict(operator_model='duration state',
                numeric_magnitude_consumer_required=False,duration_carrier_required=True,
                spatial_recipient_model_required=True,world_position_provider_required=True,
                simultaneous_status_precedence_required=True,
                force_destination_and_motion_policy_required=issue.get('stat')=='force_move',
                declared_cpu_contract=movement_contract(),
                current_world_consumer_verified=False,current_cuda_verified=False,
                default_producer_installed=False)
            result['movement_prerequisites']['current_overlap_validation']=current_movement_overlap_validation()
            if issue.get('stat')=='enemy_movement_disable':
                result['movement_prerequisites']['current_group_recertification']=current_movement_stop_validation()
        if issue.get('kind')=='buff' and issue.get('stat')=='heal_received_pct' and issue.get('target')=='all_enemies':
            result['declared_enemy_healing_contract']=dict(suite='enemy-healing-common',cases=6,
                original_roster='앤 : 미라클 페어리',original_definitions=69,
                cpu_reference_verified=True,actual_finite_ADD_health=True,existing_world_source_clock=True,
                existing_heal_received_multiplier=True,existing_recipient_generation_visibility=True,
                declarations=['literal idle source nodes','configured finite damage-owned ADD recipients','flat healing amounts'],
                gpu_wire_connected=False,metal_verified=False,current_cuda_verified=False,
                default_producer_installed=False,historical_canonical_equivalence=False,in_game_rules_verified=False)
            result['declared_enemy_healing_metal_validation']={'suite': 'enemy-healing', 'inputs': 14, 'native_cases': 6, 'rejected_cases': 8, 'metal_verified': True, 'independently_audited': True, 'evidence': 'tests/fixtures/enemy-healing-named-admission-independent-v3.json', 'evidence_sha256': '9c84d3c24bda0c654ed707a04bd63a6a4a4fcd6f6daa1a972cd74496b45bbc38', 'gpu_wire_connected': True, 'raw_fractional_credit_and_per_owner_rounding': True, 'same_generation_dead_packet_overkill_verified': True, 'current_cuda_verified': False, 'default_producer_installed': False, 'historical_canonical_equivalence': False, 'in_game_rules_verified': False, 'scope': 'Declared source-node finite ADD healing; original Anne 69 definitions, six scenarios only'}
            result['note']+=' A separate declared CPU contract now consumes the original Anne reduction in real ADD healing, preserving health ownership, damage accounting and source generations; default and GPU admission remain closed.'
        if issue.get('stat') in ('effect_range_pct','effect_target_count_add'):
            from portable_named_range_battle_evidence import validation as radial_validation
            result['declared_named_range_battle_metal_validation']=radial_validation()
        if issue.get('stat')=='effect_range_pct':
            result['declared_named_range_battle_contract']={'suite': 'named-range-battle-common', 'cases': 4, 'original_roster_definitions': 87, 'original_source_profile': '레이 (가칭)', 'source_profile_is_preview': False, 'cast_snapshot_connected': True, 'actual_actor_delivery_connected': True, 'gpu_wire_connected': False, 'metal_verified': False, 'current_cuda_verified': False, 'default_producer_installed': False, 'scope': 'Declared radial growth and canonical logical candidate order; inspect CPU reference report for execution evidence'}
            result['declared_named_range_selection']={'suite': 'named-effect-range', 'inputs': 21, 'native_cases': 12, 'rejected_cases': 9, 'original_modifier_cases': 5, 'metal_verified': True, 'independently_audited': True, 'current_cuda_verified': False, 'default_producer_installed': False, 'full_original_profile_verified': False, 'battle_damage_delivery_verified': False, 'selection_consumer_connected': True, 'model': 'named-effect-radial-growth-v1', 'evidence': 'tests/fixtures/named-effect-range-independent-v4.json', 'evidence_sha256': 'f1bb6210980e31d3a765baad2005b8be57a6ff534aacd59d7cb2d360e4e09ae2', 'in_game_radius_semantics_verified': False, 'scope': 'Final checkpoint of shared events and carriers into declared radial circle/rectangle selection only'}
        if issue.get('stat')=='effect_target_count_add':
            result['declared_physical_target_count_query']=dict(suite='named-target-count-shots',native_cases=5,rejected_cases=4,
                metal_verified=True,independently_audited=True,cuda_verified=False,physical_shot_lifetime_verified=True,
                admitted_targets=['self','all_allies'],original_modifier_definition_cases=2,
                selection_consumer_connected=False,original_full_profile_verified=False)
            result['declared_shared_target_count_query']=dict(suite='named-target-count-query',native_cases=6,rejected_cases=3,
                metal_verified=True,independently_audited=True,cuda_verified=False,physical_shot_lifetime_verified=False,
                selection_consumer_connected=False,original_full_profile_verified=False)
            result.update(contract_coverage='declared_cpu_query_and_external_shared_gpu_query',
                declared_target_count_query=dict(suite='heavyarms-target-count-native',cases=4,original_definitions=25,
                    model='named-effect-target-count-v1',reader='app/effect_target_count_policy.py:query',
                    scope='Named capacity and existing native carrier lifetime only; inspect reference evidence',
                    selection_consumer_connected=False,gpu_supported=False),
                required_extensions=['named_target_count_query_to_actual_selector','spatial_lock_and_original_full25_battle_integration','current_CUDA_and_Metal_validation'])
        if issue.get('stat')=='lock_on':
            result.update(native_consumer='generic_named_carrier_present_dedicated_lock_model_missing',contract_coverage='native_named_marker_only',
                native_marker_contract=dict(suite='heavyarms-lock-marker-native',original_definitions=25,worlds=['boss_only','three_live_adds'],
                    carrier_stack_remove_and_named_query=True,selection_scope='Canonical logical aim proxy; first live ADD in declared world, not spatial Lock On',
                    spatial_selection_verified=False,target_count_extension_verified=False,full_original_typed_projectile_verified=False,
                    marker_stack_count_is_not_distinct_target_count=True,unlocked_candidate_exclusion_verified=False,
                    published_selection_contract='tests/fixtures/heavyarms-lock-published-contract.json'),
                required_extensions=['dedicated_spatial_lock_selection_and_target_count_model','shared_marker_lifecycle_and_recipient_integration','current_CUDA_and_Metal_full_original_profile_validation'],
                note='The original full25 native profile creates a generic named marker, caps stack5, removes it on attack and filters live logical enemies by that name. This is a CPU contract; dedicated spatial Lock On selection, target-count extension and full25 typed-projectile battle remain unverified. Keep default admission closed')
        if issue.get('target')=='all_projectiles':
            result['typed_foundation_validation']=typed_foundation
            result['typed_modifier_battle_validation']=modifier_battle
            result['typed_skill_validation']=dict(suite='destructible-skill',inputs=18,native_cases=10,rejected_cases=8,original_definitions=1,original_definition_inputs=8,metal_verified=True,independently_audited=True,cuda_device_verified=False,scalar_context_declared=True,automatic_battle_dispatch_verified=False,projectile_modifiers_verified=False,original_full_profile_verified=False,in_game_rules_verified=False,
                scope='plain_original_definition_to_existing_scalar_query_and_live_projectile_producer')
            result['typed_frame_validation']=dict(suite='destructible-frame',inputs=26,native_cases=17,rejected_cases=9,metal_verified=True,independently_audited=True,ordinary_notify_and_budget_verified=True,same_stack_counter_children_verified=True,empty_targets_preserve_budget=True,full_battle_scheduler_verified=False,cuda_device_verified=False,original_full_profile_verified=False,projectile_modifiers_verified=False,
                scope='opt_in_common_skill_frame_with_explicit_typed_world_and_scalar_context')
            result['typed_original_battle_validation']=dict(suite='destructible-original-battle',inputs=8,native_cases=8,original_definitions=1,skill_levels=[1,5,10],metal_verified=True,independently_audited=True,actual_burst_notification_verified=True,per_owner_skill_levels_verified=True,original_full_profile_verified=False,cuda_device_verified=False,projectile_modifiers_verified=False,scope='one_unmodified_original_definition_on_declared_actual_battle_world')
            result['typed_battle_validation']=dict(suite='destructible-battle',inputs=44,native_cases=31,rejected_cases=13,metal_verified=True,independently_audited=True,actual_battle_scheduler_verified=True,separate_cpu_event_list=False,scalar_context_declared=True,ordinary_cleared_nodes_coexist=True,counter_threshold_and_death_verified=True,self_child_conditions_verified=True,nested_same_producer_reentry_verified=True,explicit_boss_and_generic_child_recipients_verified=True,typed_logical_enemy_policy_verified=False,canonical_targets_cleared_verified=False,cuda_device_verified=False,original_full_profile_verified=False,projectile_modifiers_verified=False,
                scope='opt_in_timed_typed_targets_on_actual_common_battle_clock_plain_skill_only')
        return result
    weapon_completion=(issue.get('phase')=='effect' and issue.get('category')=='trigger' and not issue.get('fields') and operator.get('domain')=='timing' and isinstance(operator.get('descriptor'),str) and operator['descriptor'].startswith('weapon_hit:') and bool(operator['descriptor'][len('weapon_hit:'):]))
    ordinary_stack_carrier=(issue.get('phase')=='effect' and issue.get('kind')=='buff' and issue.get('stat')=='buff_stack_add' and issue.get('target') in ('self','target') and not issue.get('fields') and issue.get('scaling') is None)
    attachment_annotation=(issue.get('phase')=='effect' and issue.get('kind')=='damage' and issue.get('stat')=='projectile_attachment_damage' and issue.get('fields')==['weapon_type'] and issue.get('scaling') is None)
    if weapon_completion or ordinary_stack_carrier or attachment_annotation:
        result.update(lane='native_contract_extension' if attachment_annotation else 'gpu_lowering_candidate',native_consumer='pinned_handler_completion_and_ordinary_carrier_activation',contract_coverage='recorded_subset',recorded_cases=26,reference_suites=['projectile-chain','projectile-chain-rosters'],original_profile_contracts=2,original_profile_definitions=87,consumer_source='app/portable_projectile_chain_contract.py; calculator/timeline.py:_handle_damage_eff; calculator/buff_manager.py:_activate,_dispatch_instant',declared_model=True,in_game_rules_verified=False,
            required_extensions=['shared_named_completion_after_gauge_and_per_hit_children','private_ordinary_buff_carrier_projection_without_instant_mutation','matching_base_weapon_binding_guard_with_mismatch_rejection','Metal_and_current_CUDA_and_old_input_retention'],
            scoped_metal_validation=dict(suite='projectile-chain-retention',inputs=492,native_cases=378,rejected_cases=114,original_profile_suite='projectile-chain-rosters',original_inputs=2,original_definitions=87,independently_audited=True),
            implemented_extensions=['shared_named_completion_after_children','ordinary_buff_carrier_identity','matching_actor_base_weapon_binding','old460_full_raw_retention'],
            note='CPU26 fixes handler completion once per cast, not per packet: zero/negative hit count still notifies, zero original coefficient and special early returns do not. Buff-kind buff_stack_add is an ordinary named carrier; only instant-kind enters stack mutation. Original Rapi87 at3/30s is observed without semantic changes; 30s has16 attachment callbacks/9 immediate explosions/one start explosion and final enemy carrier stack6. Matching MG/base metadata is observed; contradictory declarations are a reference-model gap, never an effect-local override. The private shared entry is Metal-verified for32 authored inputs and original Rapi3/30s inside retained492; public/general/current-CUDA/full-catalog certification remains incomplete')
        return result
    if issue.get('phase')=='effect' and not issue.get('fields') and issue.get('scaling') in (None,'lost_hp_pct') and ((issue.get('kind')=='buff' and issue.get('stat') in ('dmg_accum_dealt_atk_pct','dmg_accum_received_atk_pct','dmg_accum_rate_pct')) or issue.get('kind')=='damage' and issue.get('stat')=='accum_split_damage'):
        result.update(lane='native_contract_extension',native_consumer='confirmed_installed_lifecycle_and_boss_landing',contract_coverage='recorded_subset',recorded_cases=52,reference_suites=['damage-accum'],consumer_source='app/damage_accum_runtime.py; app/effect_runtime.py; calculator/buff_manager.py:accumulate_damage,_accum_rate,accum_discharge; calculator/timeline.py:_land_boss,_handle_damage_eff',declared_model=True,in_game_rules_verified=False,
            implemented_extensions=['private_shared_scalar_pool_and_global_name_archive','explicit_missing_rate_value_bit_and_ordered_base_named_sums','post_lifesteal_boss_collection_and_owned_deferred_notices','active_order_discharge_and_split_only_integer_conversion'],
            scoped_metal_validation=dict(suite='damage-accum-retention',inputs=460,native_cases=354,rejected_cases=106,new_battle_contracts=52,old398_raw_bytes_retained=1251999744,independently_audited=True),
            followup_metal_validation=dict(suite='damage-accum-rosters',inputs=4,original_definition_counts=[73,74],durations=[3,30],independently_audited=True),
            required_extensions=['capacity_and_notice_reentry_extremes','broader_aimed_part_and_parent_callback_mixtures','full_catalog_and_current_CUDA'],
            note='Native52 and private Metal460 are independently audited, including full old398 raw retention. Original Dorothy73/Trony74 definitions at3/30s match Metal/native without effect trimming. GPU observations cover complete battle/trace and final pool/archive state; detailed scalar state-operation proof is separate. Collection visits dealt then received groups, with same-owner rates and no recipient live filter; discharge takes first active matching name, else its global archive. This is scoped declared-model evidence, not full-character/game-rule certification. Current full-battle CUDA remains unverified')
        return result
    if issue.get('phase')=='effect' and not issue.get('fields') and issue.get('scaling') is None and (issue.get('kind'),issue.get('stat'),issue.get('target')) in (('buff','heal_overcharge_store_atk_pct','self'),('buff','accumulate_max_scale_pct','self'),('instant','heal_overcharge_discharge','all_allies')):
        result.update(lane='native_contract_extension',native_consumer='confirmed_installed_lifecycle',contract_coverage='recorded_subset',recorded_cases=41,reference_suites=['heal-charge','heal-charge-lifetime','heal-charge-rosters'],consumer_source='app/heal_charge_compat.py; app/effect_runtime.py; app/lifecycle_specs.py',declared_model=True,in_game_rules_verified=False,implemented_extensions=['shared_scalar_pool_and_explicit_end_retention','live_capacity_bonus_and_ordered_discharge_continuation','native_quantity_observation_before_HP_clamp'],scoped_metal_validation=dict(suite='heal-charge-retention',inputs=386,native_cases=290,rejected_cases=96,synthetic_contracts=29,old349_raw_bytes_retained=1097859072,independently_audited=True),completed_followups=['immediate_retirement_of_removed_owner_records','retention_of_persistent_and_shared_live_carriers','native41_lifetime_contracts','original_Delta79_81_definitions_at3_30s','ordered1272_quantity_and_clock_records_with_full_chain'],followup_metal_validation=dict(suite='heal-charge-lifetime-retention',inputs=398,native_cases=302,rejected_cases=96,new_lifetime_contracts=12,real_profile_inputs=4,original_definition_counts=[79,81],shared_SHA_probe_inputs=13,independently_audited=True),required_extensions=['capacity1024_and_history1048576_boundaries','broader_lazy_heal_share_and_parent_callback_mixed_queries','full_catalog_and_current_CUDA'],note='Received body healing before clamp accumulates in one scalar carrier pool; this differs from excess-healing damage storage. Native29 covers owner-order activation, owner ATK snapshot, live capacity bonus, quantity reset, end retention, cleanse/down discard and consume-before-ordered-heals. The declared model is not game-verified. Private shared admission and Metal386 are audited; Metal398 plus original Delta four inputs are independently audited, including active shared/persistent retention and all1272 observations; current CUDA, capacity stress and broader mixed queries remain unverified')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='fields' and issue.get('kind')=='damage' and issue.get('stat')=='auto_damage' and issue.get('fields')==['weapon_type']:
        result.update(lane='reference_model_gap',native_consumer='actor_weapon_only',contract_coverage='recorded_subset',reference_suites=['skill-weapon','skill-weapon-rosters'],recorded_cases=16,reference_model_gap_cases=6,
            consumer_source='calculator/timeline.py:_handle_damage_eff; app/portable_skill_weapon_contract.py',
            note='The pinned native handler reads cs.weapon and base_weapon_type, not the effect annotation. Only a known declaration equal to the caster base weapon is admitted for normal_attack auto_damage. Effect-local override or mismatched annotation semantics remain unresolved; do not infer no-op support or in-game correctness')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='fields' and issue.get('kind')=='damage' and issue.get('stat') in ('sequential_damage:6','sequential_damage:13') and issue.get('target')=='enemies_random' and issue.get('fields')==['land_in_full_burst']:
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',contract_coverage='recorded_subset',recorded_cases=15,reference_suites=['full-burst-landing','full-burst-landing-rosters'],
            consumer_source='calculator/timeline.py:_handle_damage_eff,_handle_landing_damage,BurstController.tick; app/attack_timing_specs.py:full_burst_landing',
            implemented_extensions=['tagged_private_landing_mode_in_shared_pending_arrays','cast_count_latch_and_landing_reference_read','row_based_parent_exclusion_mask','shared_frame_execution_and_bounded_receipt_range','declared_single_body_counter_selector_lowering'],
            scoped_metal_validation=dict(suite='full-burst-landing-retention',inputs=258,native_cases=186,rejected_cases=72,synthetic_contracts=13,original_profile_inputs=2,original_definitions=76,original_durations=[3,30],original_six_hit_branch_verified=True,original_thirteen_hit_branch_verified=False,independently_audited=True),
            followup_metal_validation=dict(suite='full-burst-query-retention',inputs=291,native_cases=218,rejected_cases=73,queue_capacity=512,finite_native_overflow_packets=515,overflow_gpu_status=64,query_contracts=19,query_diagnostic_suite='full-burst-query-diagnostic',query_diagnostic_inputs=19,ordered_query_events=41,zero_hit_huge_coefficient_cases=5,ignored_live_1024_cases=2,old272_raw_bytes_retained=855638016,independently_audited=True),
            completed_followups=['live_reentrant_queue_and_512_capacity','physical_landing_children_retained_for_next_collection','typed_tail_part_and_interrupt_snapshot_ownership','query_only_zero_hit_without_damage_arithmetic','live_count_read_without_unused_integer_capacity_check','pending2_HP_basis_with_immutable_parent_exclusions'],
            required_extensions=['additional_zero_coefficient_and_mixed_target_rng_contracts','low_marker_periodic_receipt_relocation','broader_worlds_full_profiles_and_current_source_cuda_validation'],
            note='Thirteen native fixtures and original Elegg Boom and Shock3/30s confirm cast-time gates/counts, landing-time buff queries, later-cast exclusions, same-frame full-burst landings and queued ordinary children. Cast reference1 is read as2 at landing before overriding back to1; preserve both calls. Original30s fires the6-hit branch;13-hit is synthetic only. Private Metal258 and original Elegg3/30s match the fixed native scope. Retained232 inputs/raw outputs are unchanged; this is not full-character or current-source CUDA certification. Follow-up Metal291 plus diagnostic19 verifies live queue512, next-collection children, zero-hit query-only, ignored live1024, and deferred HP basis with parent exclusions;41 ordered query values match. Individual514 GPU packet history is omitted in the two capacity summaries. Zero-coefficient/target mixtures, low-marker periodic receipt relocation, broader profiles and current CUDA remain unverified')
        return result
    if issue.get('phase')=='effect' and issue.get('kind')=='damage' and issue.get('stat')=='dealt_fixed_damage':
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',contract_coverage='recorded_subset',recorded_cases=23,reference_suites=['parent-fixed'],consumer_source='calculator/timeline.py:_charge_fire,_handle_damage_eff; app/quantity_specs.py',scoped_metal_validation=dict(suite='parent-fixed-retention',inputs=321,native_cases=241,rejected_cases=80,contracts=23,independently_audited=True),implemented_extensions=['notification_local_parent_damage_quantity','multiply_then_divide_then_integer_truncation','queued_zero_fraction_packet','no_second_damage_factors_named_hits_or_gauge','recipient_routing_and_generic_landing_lifecycle'],required_extensions=['broader_weapon_callback_and_target_world_mixtures','original_Emilia_full_profile_after_max_ammo_scaling','current_source_cuda_validation'],note='Scoped native23 and Metal321 use real full-charge notification dealt values, muzzle/pellet grouping, empty nested contexts, budget consumption and next-frame landing. This does not certify every producer/world combination, original Emilia or current CUDA')
        return result
    if issue.get('phase')=='effect' and issue.get('kind')=='buff' and issue.get('stat')=='charge_dmg_pct' and issue.get('scaling')=='max_ammo_count' and issue.get('fields')==['scaling'] and issue.get('target')=='self':
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',contract_coverage='recorded_subset',recorded_cases=22,reference_suites=['max-ammo-scaling','max-ammo-scaling-rosters'],scoped_metal_validation=dict(suite='max-ammo-scaling-retention',inputs=349,native_cases=261,rejected_cases=88,contracts=20,original_profile_inputs=2,original_profile_effects=73,independently_audited=True),consumer_source='calculator/buff_manager.py:get_buffs,_scale_by_max_ammo; calculator/timeline.py:CharState._full_ammo,max_ammo_provider',implemented_extensions=['native_live_recipient_capacity_query','same_recipient_recursion_skip','separate_half_up_groups_and_bankers_flat_rounding','mode_capacity_latch_and_bullet_lifetime','shared_gpu_live_capacity_value_source','original_Emilia_full_profile_3s_30s'],required_extensions=['broader_late_query_target_and_mode_transition_mixtures','additional_scaled_numeric_stats','current_source_cuda_validation'],note='Twenty native contracts and the complete original Emilia profile at3/30s now match shared Slang/Metal. CapacityFromParts is shared; scaling uses the raw capacity dependency to avoid publishing an incomplete dictionary or recursive code generation. Private charge-damage scope only; broader query mixtures and current CUDA remain unverified')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='trigger' and isinstance(issue.get('operator'),dict) and issue['operator'].get('domain')=='timing' and issue['operator'].get('descriptor') in ('multi_hit:2','multi_hit:4'):
        result.update(lane='reference_model_gap',native_consumer='listener_without_battle_producer',native_consumer_scope='default-battle',scoped_native_consumer='actual-normal-shot-group',reference_suites=['attack-group-battle'],scoped_metal_validation=dict(suite='attack-group-battle',inputs=32,native_cases=22,rejected_cases=10,actual_shot_groups=168,threshold_notifications=112,independently_audited=True,game_geometry_verified=False),consumer_source='app/battle_attack_group_runtime.py; gpu/attack_group_runtime.slang; app/portable_missing_consumer_audit.py',note='Explicit attack groups count distinct typed targets; the default battle does not open/seal these groups and publishes default attack_id0. Pellet count, total damage or manual group tests cannot replace a real producer. An opt-in CPU producer now captures actual normal-shot returns and body/add landings under declared all-logical-enemies routing, including nonzero original children and frozen generations; see reference attack-group-battle. This routing is not verified game geometry. Shared Slang now connects owned physical-shot groups, frozen queued children and current-target buffs under this explicit policy; Metal32 including ADD quantities and rejected inputs is independently verified. Default admission, broader geometry and current CUDA remain closed')
        result['declared_logical_actor_geometry_contract']=dict(suite='logical-actor-geometry-common',cases=6,
            original_roster='벨로타',prepared_roster_definitions=68,original_multi_hit4_connected=True,
            cpu_reference_verified=True,existing_sampled_pellet_and_actor_landing=True,
            part_excluded_from_enemy_count=True,declared_geometry_only=True,
            gpu_wire_connected=False,metal_verified=False,cuda_verified=False,
            historical_canonical_equivalence=False,in_game_rules_verified=False)
        result['declared_logical_actor_geometry_metal_validation']=dict(
            suite='logical-actor-geometry',inputs=13,native_cases=6,rejected_cases=7,
            original_roster='벨로타',original_roster_definitions=68,
            actual_BODY_ADD_geometry=True,part_excluded_from_enemy_count=True,
            metal_verified=True,independently_audited=True,current_cuda_verified=False,
            declared_model_only=True,default_producer_installed=False,
            historical_canonical_equivalence=False,in_game_rules_verified=False,
            evidence='tests/fixtures/logical-actor-independent-v1.json',
            evidence_sha256='533334e9533a45aedd4857e43d404519c34dd350d185de53a73f8c0a7779383e')
        result['shared_delivery_recertification']=dict(
            source_commit='5433f8e97f2368c1abb54b15be9f2206fd6f3998',
            suites=['logical-actor-geometry','logical-actor-rosters'],inputs=18,native_cases=11,rejected_cases=7,
            independently_audited=True,all_old_input_and_readback_bytes_retained=True,
            includes_post_death_shot_regression=False,current_cuda_verified=False,
            default_producer_installed=False,full_character_verified=False,
            evidence=[dict(path='tests/fixtures/logical-named-admission-independent-v3.json',
                           sha256='8f56c2e6c85eddb7dc9d13ebd5a8462c1752b8589ae802ac027af8b0a55ba9b9'),
                      dict(path='tests/fixtures/rosters-named-admission-independent-v3.json',
                           sha256='78d859f0f030b4f0f1fd43f3ec72c99e1034d7b8791773ff53c15221bc70770b')])
        if issue['operator']['descriptor']=='multi_hit:2':
            result['declared_logical_actor_roster_validation']=dict(
                suite='logical-actor-rosters',original_roster='니힐리스타',original_roster_definitions=70,
                inputs=5,native_cases=5,metal_verified=True,independently_audited=True,
                rotated_rectangle_verified=True,actual_PART_exclusion=True,
                current_cuda_verified=False,default_producer_installed=False,
                in_game_rules_verified=False,full_character_verified=False,
                evidence='tests/fixtures/logical-Nihilister-independent-v1.json',
                evidence_sha256='84540782b106c153ade02a448d709fcda395a56c2dd83c7142fb95078155b887')
        result['reference_suites'].append('attack-group-native-route')
        result['reference_suites'].append('attack-group-long')
        result['long_group_metal_validation']=dict(suite='attack-group-long',inputs=60,native_cases=48,rejected_cases=12,long180s_cases=6,new_full_group_records=927,omitted_group_records=0,old53_full_raw_retained=True,independently_audited=True,compact_history='lossless_variable_records_after_schema_landing_bank',current_cuda_verified=False)

        result['native_route_metal_validation']=dict(suite='attack-group-native-route',inputs=53,native_cases=42,rejected_cases=11,new_native_routing_cases=20,original_battle_baselines=16,per_pellet_reselection_cases=2,old32_full_raw_retained=True,independently_audited=True,game_geometry_verified=False,current_cuda_verified=False)
        result['note']+=' A separate native-routing policy now uses the existing physical selector for every pellet, including sequential ADD destruction within one real SG shot. Metal53 is independently audited; the extra20 cases preserve native routing and16 unchanged full battles. This does not certify geometry or install the default producer.'
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
            published_allocation=dict(evidence='tests/fixtures/bay-published-allocation-v1.json',
                evidence_sha256='7e8a7c3f131da05beba015a557af63fe9e8d88f73b60c39ad2193aed94544ba4',
                body_weight_candidate=[8,3],cover_weight_candidate=262,
                ratios_are_inferred_from_rounded_tables=True,exact_cover_weight_verified=False,
                native_consumer_implemented=False,in_game_rules_verified=False,gpu_supported=False),
            required_extensions=['exact_allocation_and_arithmetic_contract','original_carrier_and_separate_cover_recipient',
                'existing_incoming_layer_and_callback_order','cover_break_restoration_and_caster_death',
                'shared_CUDA_Metal_full_original_profile_validation'],
            note='Published tables now support an 8:3 body-weight candidate and an approximate cover weight. The one-member cover row does not agree with nearest rounding of the candidate. Exact cover arithmetic, layer/callback order and favorite-stage behavior remain unverified; keep canonical rejection. Do not alias to even sharing or accept as no-op')
    elif stat=='heal_split':
        result.update(native_consumer='declared_cpu_model',consumer_source='app/heal_sharing_compat.py',
            contract_coverage='recorded_subset',reference_suites=['heal-share','heal-share-extended','heal-share-targets','heal-share-lifesteal'],recorded_cases=43,
            lane='native_contract_extension',note='Declared model choices still need in-game confirmation; contracts are not exhaustive')
        if issue.get('category')=='effect' and not issue.get('fields') and issue.get('scaling') is None and issue.get('target') in ('self','all_allies'):
            result['lane']='gpu_lowering_candidate'
    elif stat in ('projectile_dmg_pct','shield_dmg_pct'):
        result.update(lane='reference_model_gap',native_consumer='explicitly_missing_target_world',
            typed_foundation_validation=typed_foundation,
            typed_modifier_design=dict(reference_suite='destructible-modifier',cases=20,declared_model='v1',cpu_contract_verified=True,canonical_consumer_verified=False,metal_verified=True,metal_suite='destructible-modifier',metal_inputs=29,metal_native_cases=20,independently_audited=True,cuda_device_verified=False,battle_connected=False,in_game_rules_verified=False,scope='private_declared_scalar_query_only'),
            consumer_source='research/upstream/nikke-calc-master/docs/IMPL-STATUS.md; calculator/timeline.py:_handle_damage_eff; app/portable_missing_consumer_audit.py',
            note='The pinned specification explicitly leaves destructible enemy projectiles and enemy shields unimplemented. all_projectiles returns before damage handling; these modifiers have no canonical damage-factor consumer. A private v1 CPU/Metal scalar contract adds the explicitly declared target-kind contribution inside factor5 before final rounding; the scalar probe itself is not a battle producer and does not certify in-game rules. Separate opt-in plain projectile, HP-shield and hit-credit skill bindings are recorded when applicable; their scopes do not establish weapon or piercing interception. This remains missing reference semantics, never no-op GPU support. Historical decisions are evidence, not instructions to omit the current goal')
        result['typed_original_modifier_validation']=dict(suite='original-modifier-probe',inputs=19,native_cases=19,
            axis_cases=10 if stat=='projectile_dmg_pct' else 9,original_carrier_profiles=4,
            metal_verified=True,independently_audited=True,original_definitions_preserved=True,
            explicit_added_damage_probe=True,automatic_weapon_aim_verified=False,coordinates_verified=False,
            canonical_consumer_verified=False,cuda_device_verified=False,in_game_rules_verified=False,
            full_character_verified=False,scope='declared_v1_original_carrier_to_explicit_typed_probe_only')
        result['typed_coordinate_modifier_validation']=dict(suite='coordinate-typed',inputs=10,native_cases=10,
            axis_cases=4 if stat=='projectile_dmg_pct' else 5,original_carrier_profiles=3 if stat=='projectile_dmg_pct' else 4,
            coordinate_battle_connected=True,one_resident_runtime=True,shared_world_clock=True,shared_sampled_rng=True,
            explicit_added_damage_probe=True,metal_verified=True,independently_audited=True,
            automatic_typed_weapon_aim_verified=False,canonical_consumer_verified=False,cuda_device_verified=False,
            in_game_rules_verified=False,full_character_verified=False,scope='declared_typed_attack_in_complete_original_coordinate_battle')
        result['typed_spatial_modifier_validation']=dict(suite='coordinate-typed-geometry',inputs=28,native_cases=18,
            added_spatial_cases=8,axis_spatial_cases=7 if stat=='projectile_dmg_pct' else 1,
            metal_verified=True,independently_audited=True,shared_shape_math=True,live_world_generation_selection=True,
            explicit_point_and_extra_attack=True,automatic_typed_weapon_aim_verified=False,
            canonical_consumer_verified=False,cuda_device_verified=False,in_game_rules_verified=False,
            full_character_verified=False,scope='declared_point_skill_selects_live_typed_target_before_damage')
        result['typed_live_aim_validation']=dict(suite='coordinate-typed-live-aim',inputs=35,native_cases=22,
            added_live_aim_cases=4,axis_live_aim_cases=3 if stat=='projectile_dmg_pct' else 1,
            canonical_aim_bank_consumer_verified=True,previous_frame_skill_aim_verified=True,
            explicit_added_damage_probe=True,declared_aim_operation_cases=3,
            metal_verified=True,independently_audited=True,automatic_typed_weapon_aim_verified=False,
            canonical_consumer_verified=False,cuda_device_verified=False,in_game_rules_verified=False,
            full_character_verified=False,scope='canonical_live_aim_supplies_declared_typed_skill_selector')
        result['typed_coordinate_weapon_reference']=dict(suite='coordinate-typed-weapon-common',cases=7,
            cpu_contract_verified=True,original_weapons_and_effects_preserved=True,
            actual_sampled_pellets=True,frozen_shot_targets=True,deferred_typed_landing=True,
            shared_rng_state_verified=True,full_charge_parent_quantity_verified=True,
            metal_verified=False,cuda_device_verified=False,automatic_typed_weapon_aim_verified=False,
            canonical_consumer_verified=False,in_game_rules_verified=False,full_character_verified=False,
            next_stage='typed_auto_aim_and_gameplay_reference',scope='declared_typed_geometry_inside_actual_native_weapon_packets')
        result['typed_coordinate_weapon_validation']=dict(suite='coordinate-typed-weapon',inputs=46,native_cases=29,
            new_weapon_cases=7,original_definitions_preserved=True,actual_sampled_weapon_packets=True,
            frozen_shot_handles=True,real_landing_order=True,canonical_and_typed_depth_merge=True,
            retained_physical_receipts=2048,all_physical_receipts_hashed=True,
            metal_verified=True,independently_audited=True,prior35_all_output_bytes_retained=True,
            automatic_typed_weapon_aim_verified=False,canonical_consumer_verified=False,
            cuda_device_verified=False,in_game_rules_verified=False,full_character_verified=False,
            scope='declared_v1_static_typed_shapes_inside_original_sampled_weapon_production')
        if stat=='projectile_dmg_pct':
            result['original_physical_projectile_modifier_validation']=dict(suite='original-projectile-weapons',inputs=13,native_cases=8,rejected_cases=5,
                original_profiles=['Sakura','Anchor','Clay'],durations_seconds=[3,12,30],original_weapons_effects_and_owners_preserved=True,
                explicit_added_damage_probe=False,automatic_typed_weapon_aim_verified=True,body_owner_explicit=True,physical_kind_preserved=True,
                self_and_all_allies_recipients_verified=True,original_count_full_burst_proc_and_expiry_verified=True,
                total_physical_receipts=5367,maximum_case_physical_receipts=2186,retained_physical_receipts_per_case=2048,all_physical_receipts_hashed=True,
                metal_verified=True,independently_audited=True,cuda_device_verified=False,canonical_consumer_verified=False,
                nearby_selector_verified=False,in_game_rules_verified=False,full_character_verified=False,public_admission=False,
                evidence='research/target-count-query-evidence/metal-original-projectile-weapons-v1.json',
                scope='original_physical_weapons_in_declared_body_owned_typed_world')
        else:
            result['original_physical_shield_modifier_validation']=dict(suite='original-shield-weapons',inputs=15,native_cases=10,rejected_cases=5,
                original_profiles=['Rei','Asuka','Mari','Misato'],parsed_stat_carriers=4,durations_seconds=[3,12,22,30],
                original_weapons_effects_and_owners_preserved=True,original_growth_config_preserved=True,explicit_added_damage_probe=False,
                automatic_typed_weapon_aim_verified=True,body_owner_explicit=True,physical_kind_preserved=True,
                self_and_all_allies_recipients_verified=True,full_charge_and_passive_state_proc_verified=True,
                explicit_cover_cases=2,cover_expiry_and_reactivation_verified=True,original_controls_preserved_in_cover_cases=False,
                total_physical_receipts=9237,maximum_case_physical_receipts=2457,retained_physical_receipts_per_case=2048,all_physical_receipts_hashed=True,
                metal_verified=True,independently_audited=True,metal_pipeline_required_cache_hit=True,cuda_device_verified=False,
                canonical_consumer_verified=False,piercing_multi_target_verified=False,parts_verified=False,
                in_game_rules_verified=False,full_character_verified=False,public_admission=False,
                evidence='research/target-count-query-evidence/metal-original-shield-weapons-v1.json',
                scope='original_physical_weapons_and_cover_in_declared_body_owned_hp_shield_world')
        result['typed_owner_field_reference']=dict(suite='coordinate-typed-owner-common',cases=5,
            original_profile='Prim',original_definitions=71,declared_counter_audit_effects=2,
            cpu_reference_verified=True,body_owner_required=True,physical_handle_preserved=True,
            ordinary_current_field_receivers_verified=True,counter_owner_distinct_from_aim_verified=True,
            stale_and_unknown_owners_rejected=True,gpu_wire_connected=False,metal_verified=False,
            cuda_device_verified=False,canonical_consumer_verified=False,in_game_rules_verified=False,
            full_character_verified=False)
        result['typed_owner_field_validation']=dict(suite='coordinate-typed-owner',inputs=80,native_cases=45,
            rejected_cases=35,original_profile='Prim',original_definitions=71,declared_counter_audit_effects=2,
            declared_actor_policy='body-owned-current-fields-v1',body_owner_required=True,
            original_current_field_counts=[0,1,1,1,1],physical_handle_preserved=True,
            counter_owner_distinct_from_aim_verified=True,actual_body_received_dmg_pct=17,
            actual_add_received_dmg_pct=[0,0],gpu_wire_connected=True,metal_verified=True,
            independently_audited=True,prior67_all_input_native_output_retained=True,
            gpu_live_hp_shield_counter_generation_verified=True,projectile_owner_field_battle_verified=False,
            gpu_dead_counter_generation_verified=False,gpu_stale_counter_rejection_verified=False,
            add_owner_verified=False,cuda_device_verified=False,canonical_consumer_verified=False,
            in_game_rules_verified=False,full_character_verified=False,
            scope='explicit_BODY_owned_HP_shield_current_fields_and_actual_counter_completion_with_original_full_roster')
        result['typed_owner_lifecycle_validation']=dict(suite='coordinate-typed-owner-lifecycle',inputs=88,
            native_cases=53,rejected_cases=35,new_lifecycle_cases=8,original_definitions=71,
            cpu_reference_verified=True,metal_verified=True,independently_audited=True,
            projectile_owner_field_battle_verified=True,dead_owner_query_verified=True,
            second_generation_counter_verified=True,late_stale_counter_suppression_verified=True,
            physical_identity_preserved=True,prior80_all_input_native_output_retained=True,
            warm_metal_pipeline_verified=True,slang_compiler_calls=0,
            gpu_stale_context_rejection_verified=False,add_owner_verified=False,cuda_device_verified=False,
            canonical_consumer_verified=False,in_game_rules_verified=False,full_character_verified=False,
            scope='declared_BODY_owned_projectile_and_HP_shield_live_dead_reentry_and_stale_filter_contracts')
        result['typed_logical_owner_reference']=dict(suite='coordinate-typed-logical-owner-common',cases=3,
            declared_actor_policy='logical-owned-current-fields-v1',original_definitions=71,
            cpu_reference_verified=True,explicit_add_owner=[5,1,1],physical_handle_preserved=True,
            actual_received_damage_pct=[0,0,17],shared_battle_registry_connected=True,
            stale_unknown_unspawned_owner_unit_rejected=True,gpu_wire_connected=False,
            metal_verified=False,cuda_device_verified=False,in_game_rules_verified=False,
            full_character_verified=False,scope='declared_ADD_owned_projectile_and_HP_shield_real_counter_children_CPU_only')
        result['typed_logical_owner_validation']=dict(suite='coordinate-typed-logical-owner',inputs=99,
            native_cases=56,rejected_cases=43,new_original_roster_cases=3,original_definitions=71,
            cpu_reference_verified=True,metal_verified=True,independently_audited=True,
            declared_actor_policy='logical-owned-current-fields-v1',explicit_add_owner=[5,1,1],
            ordinary_field_actor=[5,0,1],actual_received_damage_pct=[0,0,17],
            physical_handle_preserved=True,dead_typed_target_query_verified=True,
            owner_generation_mismatch_after_landing_rejected=True,prior88_all_input_native_output_retained=False,
            prior88_retention_verified_before_temp_loss=True,saved_raw_available=False,
            verification_state='historical_metal_success_raw_unavailable_after_temp_loss',
            current_host_gpu_reverified=False,
            compiler_certificate_from_same_audit=True,slang_compiler_calls_during_execution=0,
            new_shader_warm_metal_pipeline_verified=False,add_respawn_battle_verified=False,
            dead_add_field_lifetime_battle_verified=False,cuda_device_verified=False,
            canonical_consumer_verified=False,in_game_rules_verified=False,full_character_verified=False,
            scope='declared_ADD_owned_projectile_and_HP_shield_real_counter_children_and_exact_owner_generation')
        result['typed_owner_add_lifetime_reference']=dict(suite='coordinate-typed-owner-add-lifetime-common',cases=4,
            cpu_reference_verified=True,original_definitions=71,declared_audit_effects=2,
            graph_exit_before_and_after_child_verified=True,old_field_hidden_on_live_new_generation=True,
            second_generation_owner_activation_verified=True,passive_observer_transparency_verified=True,
            physical_handle_preserved=True,shared_input_packing_verified=True,
            gpu_battle_validation_pending=True,metal_verified=False,cuda_device_verified=False,
            hp_damage_death_verified=False,in_game_rules_verified=False,full_character_verified=False,
            scope='declared_ADD_graph_exit_and_reentry_CPU_contracts_only')
        result['typed_owner_add_lifetime_validation']=dict(suite='coordinate-typed-owner-add-lifetime',inputs=103,
            native_cases=60,rejected_cases=43,new_original_roster_cases=4,original_definitions=71,
            metal_verified=True,independently_audited=True,proof_host_metal_verified=True,
            graph_exit_before_after_child_verified=True,field_owner_generation_preserved=True,
            old_field_hidden_on_live_generation9=True,second_generation_owner_activation_verified=True,
            final_gpu_queries_verified=True,per_frame_visibility_trace_on_gpu_verified=False,
            old99_input_native_and_recorded_output_hashes_verified=True,new103_capture_retained_on_proof_host=True,
            prior_original99_capture_recovered=False,compiler_certificate_from_same_audit=True,
            slang_compiler_calls_during_execution=0,new_shader_warm_pipeline_verified=False,
            cuda_device_verified=False,hp_damage_death_verified=False,in_game_rules_verified=False,
            canonical_consumer_verified=False,full_character_verified=False,
            scope='declared_ADD_graph_exit_and_reentry_with_immutable_field_generation_and_final_GPU_queries')
        result['typed_owner_hp_death_reference']=dict(suite='coordinate-typed-owner-hp-death-common',cases=3,
            cpu_reference_verified=True,original_definitions=71,declared_audit_effects=2,
            finite_hp_death_while_graph_active_verified=True,same_packet_child_then_death_verified=True,
            death_before_late_child_verified=True,visible_field_before_later_death_verified=True,
            physical_handle_and_owner_generation_preserved=True,passive_observer_transparency_verified=True,
            shared_input_packing_verified=True,metal_verified=False,cuda_device_verified=False,
            canonical_consumer_verified=False,in_game_rules_verified=False,full_character_verified=False,
            scope='finite_HP_ADD_kills_CPU_contracts_only_not_graph_exit_or_hit_count_retirement')
        result['typed_owner_hp_death_validation']=dict(suite='coordinate-typed-owner-hp-death',inputs=106,
            native_cases=63,rejected_cases=43,metal_verified=True,independently_audited=True,
            gpu_damage_retirement_reason_verified=True,final_hp_damage_alive_and_owner_generation_verified=True,
            final_owned_field_hidden=True,old103_original_raw_byte_prefix_preserved=True,
            new_capture_retained_on_proof_host=True,compiler_certificate_from_same_audit=True,
            warm_metal_pipeline_verified=True,pipeline_archive_compiles_during_run=0,
            per_frame_visibility_trace_on_gpu_verified=False,graph_active_at_kill_is_cpu_witness_only=True,
            cuda_device_verified=False,in_game_rules_verified=False,canonical_consumer_verified=False,
            full_character_verified=False,scope='finite_HP_ADD_damage_kills_and_owned_field_final_GPU_state')
        result['resident_arc_validation']=dict(suite='coordinate-resident-arc',inputs=106,
            native_cases=63,rejected_cases=43,metal_verified=True,independently_audited=True,
            input_words=115680,output_words=2064786,arc_scratch_words=32786,
            all_previous_banks_retained=True,runtime_reflection_unchanged=True,
            evidence='research/resident-arc-arena-evidence/independent-v2.json',
            evidence_sha256='b6d1cda306d31537d999b6180a3bc6d900fc5d573efcf737cf997d24d31667d3',
            cuda_device_verified=False,canonical_consumer_verified=False,full_character_verified=False,
            scope='complete_private106_with_resource_backed_arc_storage; not full CUDA or public admission')
        result['resident_frames_validation']=dict(suite='coordinate-resident-frames',inputs=106,
            native_cases=63,rejected_cases=43,metal_verified=True,independently_audited=True,
            frame_slots=32,extra_runtime_bytes=4096,runtime_stride=143048,
            prior_runtime_fields_unchanged=247,all_old_raw_bytes_preserved=875469264,
            evidence='research/resident-dispatch-frame-evidence/independent106.json',
            evidence_sha256='a8678140c094a8cdfab78453d206f638ae57c19c4e251c188571ffb6bfbe3440',
            cuda_device_verified=False,cuda_physical_stack_reduction_verified=False,
            canonical_consumer_verified=False,full_character_verified=False,
            scope='complete_private106_with_resource_backed_dispatch_frames; not full CUDA or public admission')
        from portable_resident_validation import validation as resident_validation
        result['resident_storage_validation']=resident_validation()
        result['standalone_landing_cuda_validation']=dict(suite='coordinate-landing-arena-cache-only',
            inputs=40,native_cases=26,rejected_cases=14,metal_cuda_comparison_entries_equal=True,
            required_cubin_cache_hit=True,nvrtc_calls=0,compiler_library_requests=0,
            launch_sync_readback_verified=True,full_resident_battle_verified=False,
            overall_stage_passed=False,preservation_status='unverified_service_identification',
            evidence='research/coordinate-arc-arena-evidence/windows-landing-cache-v4/comparison.json',
            evidence_sha256='666f29181dc43bd7bdabdd4287b6f3a267ee1195e7f3348711f2b96b02af60b2',
            transport_evidence='research/coordinate-arc-arena-evidence/windows-landing-cache-v4/summary.json',
            transport_evidence_sha256='fd3d3464a0d18825c6e044f4bf5d6e67e2f2a4ad16e2b9079c96f528bd16bd90',
            full_character_verified=False,
            scope='standalone40_saved_Windows_comparison_fingerprints_matched_to_Metal; original_CUDA_raw_retained_on_Windows')
        result['typed_current_damage_validation']=dict(suite='coordinate-typed-actor',inputs=67,native_cases=40,
            declared_actor_policy='canonical-current-damage-v1',original_profile='Rei',original_definitions=73,
            original_current_skill_events=[0,5,5,5],literal_selector='enemies_nearest_in_range',
            current_damage_connected=True,enemy_field_ownership_connected=False,
            metal_verified=True,independent_audit_verified=True,cuda_device_verified=False,
            canonical_consumer_verified=False,in_game_rules_verified=False,full_character_verified=False,
            scope='original_current_damage_with_declared_static_typed_aim_and_body_add_receivers')
        result['typed_coordinate_aim_validation']=dict(suite='coordinate-typed-aim',inputs=59,native_cases=36,
            cpu_reference_verified=True,gpu_wire_connected=True,metal_verified=True,independent_audit_verified=True,
            declared_policy='typed-before-body-v1',typed_slots=128,focus_id_bits=9,logical_add_id=257,
            current_enemy_recipient_connected=False,cuda_device_verified=False,canonical_consumer_verified=False,
            in_game_rules_verified=False,full_character_verified=False)
        result['typed_coordinate_aim_reference']=dict(suite='coordinate-typed-aim-common',cases=7,
            positive_contract_cases=6,logical_recipient_gap_cases=1,cpu_contract_verified=True,
            canonical_arbitration_preserved=True,frame_candidates_verified=True,manual_namespace_verified=True,
            ordinary_skill_geometry_preserved=True,logical_gap_selector='enemies_nearest_in_range',
            gpu_wire_connected=False,metal_verified=False,cuda_device_verified=False,
            canonical_consumer_verified=False,in_game_rules_verified=False,full_character_verified=False,
            scope='declared_typed_before_body_frame_candidates_with_existing_manual_and_focus_resolver')
        if stat=='projectile_dmg_pct':result['typed_modifier_battle_validation']=modifier_battle
        if stat=='shield_dmg_pct':
            result['typed_shield_battle_validation']=dict(suite='destructible-shield-battle',inputs=88,native_cases=58,rejected_cases=30,new_shield_cases=15,metal_verified=True,independently_audited=True,actual_scheduler_verified=True,same_frame_stack=True,explicit_boss_owner_generation=True,no_overflow=True,body_fallback=True,named_children=True,death_counter_children=True,respawn_generations=True,weapon_interception_verified=False,hit_shield_interception_verified=False,piercing_interception_verified=False,cuda_device_verified=False,in_game_rules_verified=False,original_full_profile_verified=False,scope='declared_plain_boss_skill_hp_shield_interception_only')
            result['typed_hit_shield_battle_validation']=dict(suite='destructible-hit-shield',inputs=111,native_cases=76,rejected_cases=35,new_credit_cases=18,metal_verified=True,independently_audited=True,same_frame_stack=True,damage_and_credit_independent=True,plain_skill_hit_shield_interception_verified=True,hp_and_hit_slot_order_verified=True,prior88_all_input_native_and_raw_retained=True,weapon_interception_verified=False,piercing_interception_verified=False,cuda_device_verified=False,in_game_rules_verified=False,original_full_profile_verified=False,scope='opt_in_declared_plain_boss_skill_hit_credit_policy')
            result['typed_weapon_shield_battle_validation']=dict(suite='destructible-weapon-shield',inputs=141,native_cases=98,rejected_cases=43,new_weapon_cases=22,metal_verified=True,independently_audited=True,shot_factors_frozen=True,per_pellet_live_selection=True,hp_hit_body_continuation=True,auto_charge_tap_modes_muzzles_verified=True,ammo_and_gauge_verified=True,prior111_all_input_native_and_raw_retained=True,coordinates_verified=False,parts_verified=False,piercing_interception_verified=False,lifesteal_accumulation_verified=False,add_owner_verified=False,cuda_device_verified=False,in_game_rules_verified=False,original_full_profile_verified=False,scope='opt_in_declared_single_boss_weapon_hp_hit_shield_policy')
            result['typed_roster_skill_battle_validation']=dict(suite='destructible-skill-retention',inputs=157,native_cases=102,rejected_cases=55,original_profile='레이',original_skill_definitions=7,prepared_roster_definitions=73,new_original_roster_cases=4,metal_verified=True,independently_audited=True,original_selector_and_family_flags_preserved=True,hp_hit_body_skill_continuation=True,prior141_all_input_native_raw_retained=True,misato2_all_input_native_raw_retained=True,aoe_burst_positive_case_verified=False,coordinates_or_parts_verified=False,piercing_verified=False,lifesteal_accumulation_verified=False,multi_actor_world_verified=False,cuda_device_verified=False,in_game_rules_verified=False,original_full_profile_verified=False,scope='declared_single_boss_original_plain_and_burst_skill_hp_hit_shield_policy')
            result['typed_aoe_burst_shield_validation']=dict(suite='destructible-aoe-burst-rosters',inputs=18,native_cases=16,rejected_cases=2,metal_verified=True,independently_audited=True,aoe_burst_positive_case_verified=True,aoe_specific_modifier=435.6,allied_shield_modifier=150.,hp_hit_slot_order_and_body_fallback=True,original_roster_definitions=[78,83],original_selectors_and_family_flags_preserved=True,prior14_all_input_native_raw_retained=True,cuda_device_verified=False,piercing_verified=False,lifesteal_accumulation_verified=False,in_game_rules_verified=False,original_full_profile_verified=False,scope='declared_single_boss_original_aoe_burst_and_hp_hit_shield_mixtures')
            result['typed_body_lifesteal_shield_validation']=dict(suite='destructible-body-lifesteal-retention',inputs=31,native_cases=26,rejected_cases=5,metal_verified=True,independently_audited=True,body_only_lifesteal=True,original_milk_definitions=4,prepared_definitions=77,actual_healing_totals_checked=True,body_hp_and_capped_healing_verified=True,old_aoe18_all_input_native_raw_retained=True,old_lifesteal13_relocated_scratch_address_cases=6,accumulation_verified=False,heal_sharing_verified=False,piercing_verified=False,cuda_device_verified=False,in_game_rules_verified=False,original_full_profile_verified=False,scope='declared_single_boss_unshared_body_lifesteal_after_hp_hit_shield_interception')
            result['typed_weapon_shield_battle_validation']['original_roster_validation']=dict(suite='destructible-weapon-rosters',profile='미사토',inputs=2,durations_seconds=[3,30],original_skill_definitions=5,prepared_definitions=71,positive_shield_modifier_packets=22,positive_heal_deliveries=10,metal_verified=True,independently_audited=True,declared_single_boss_world=True,full_character_verified=False,cuda_device_verified=False)
            result['note']+=' Earlier non-coordinate weapon proof covers frozen shot factors, per-pellet HP/hit/body selection and auto/charge/tap/mode/muzzle contracts. That scope does not establish coordinates, parts, piercing, post-landing lifesteal/accumulation, per-target defense or full profiles; current coordinate evidence is recorded separately.'
    elif stat=='cover_def_pct':
        from effect_spec import SCOPED_INERT
        if stat in SCOPED_INERT:
            result.update(lane='reference_model_gap',native_consumer='scoped_inert_in_current_model',
                consumer_source='app/effect_spec.py:SCOPED_INERT',note='Clarify incoming-cover semantics before GPU lowering')
            result['declared_cover_defense_numeric']=dict(suite='cover-defense-numeric',inputs=572,native_cases=562,rejected_cases=10,
                metal_verified=True,independently_audited=True,cuda_verified=False,
                independent_base_quantity=True,original_carrier_reader_unit_verified=True,
                cover_layer_connected=False,original_full_battle_verified=False,in_game_level_curve_verified=False,
                evidence='tests/fixtures/cover-defense-numeric-metal-v1.json',evidence_sha256='75fb68d3b1f892838e847b754001dc1032bec134f5b2d01a9d5cedaef94f89ce',
                scope='Declared scalar formula and original CPU carrier read only; keep canonical/default rejection')
            result['declared_cover_defense_battle_cpu']=dict(suite='cover-defense-common',cases=4,
                actual_cover_receipts=51,actual_incoming_recipient_rows=76,private_cpu_reference_verified=True,
                explicit_independent_bases=True,original_protection_phase_preserved=True,
                gpu_wire_connected=False,metal_battle_verified=False,cuda_battle_verified=False,
                canonical_default_changed=False,in_game_rules_verified=False,
                evidence='tests/fixtures/cover-defense-battle-cpu-v1.json',evidence_sha256='b87220780a289bc1efd9752c9c2f87f9b6380e623f1278cc2709eb5b18da6d84',
                scope='Opt-in original executor extension; explicit cover base and received snapshot policy, not canonical or game equivalence')
            result['required_extensions']=['explicit_cover_base_quantity_or_verified_level_curve',
                'distinct_cover_and_body_damage_with_existing_protection_callback_order',
                'original_ranked_carrier_and_actual_cover_break_restore_battle_validation',
                'current_shared_CUDA_Metal_battle_validation']
    return result


def work_lanes(priorities):
    """Indexes into the unchanged frequency ranking; no predicted unlock counts."""
    lanes={name:[] for name in ('gpu_lowering_candidate','native_contract_extension','native_consumer_research','reference_model_gap','reference_review')}
    for index,row in enumerate(priorities):lanes[row['reference_readiness']['lane']].append(index)
    return lanes
