"""CPU-only native contract stage, before portable admission or GPU execution."""
import copy,hashlib,importlib,json,platform,sys,time
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
REFERENCES={'projectile-chain-rosters':('portable_projectile_chain_roster_cases','world_projectile_chain_native','portable_projectile_chain_contracts'),'projectile-chain':('portable_projectile_chain_cases','world_projectile_chain_native','portable_projectile_chain_contracts'),'damage-accum':('portable_damage_accum_cases','world_damage_accum_native','portable_damage_accum_contracts'),'heal-charge-rosters':('portable_heal_charge_roster_cases','world_heal_charge_roster_native','portable_heal_charge_roster_contracts'),'heal-charge-lifetime':('portable_heal_charge_lifetime_cases','world_heal_charge_lifetime_native','portable_heal_charge_lifetime_contracts'),'heal-charge':('portable_heal_charge_cases','world_heal_charge_native','portable_heal_charge_contracts'),'max-ammo-scaling-rosters':('portable_max_ammo_scaling_roster_cases','world_max_ammo_scaling_roster_native','portable_max_ammo_scaling_roster_contracts'),'max-ammo-scaling':('portable_max_ammo_scaling_cases','world_max_ammo_scaling_native','portable_max_ammo_scaling_contracts'),'parent-fixed':('portable_parent_fixed_cases','world_parent_fixed_native','portable_parent_fixed_contracts'),'full-burst-landing':('portable_full_burst_landing_cases','world_full_burst_landing_native','portable_full_burst_landing_contracts'),
            'full-burst-landing-rosters':('portable_full_burst_landing_roster_cases','world_full_burst_landing_roster_native','portable_full_burst_landing_roster_contracts'),
            'named-enemy-removal-rosters':('portable_named_enemy_removal_roster_cases','world_named_enemy_removal_roster_native','portable_named_enemy_removal_roster_contracts'),
            'named-enemy-removal':('portable_named_enemy_removal_cases','world_named_enemy_removal_native','portable_named_enemy_removal_contracts'),
            'named-enemy':('portable_named_enemy_cases','world_named_enemy_native','portable_named_enemy_contracts'),
            'random-cleanse-budget':('portable_random_cleanse_budget_cases','world_random_cleanse_native','portable_random_cleanse_budget_contracts'),
            'random-cleanse-rosters':('portable_random_cleanse_roster_cases','world_random_cleanse_roster_native','portable_random_cleanse_roster_contracts'),
            'random-cleanse-mixed':('portable_random_cleanse_mixed_cases','world_random_cleanse_native','portable_random_cleanse_mixed_contracts'),
            'random-cleanse':('portable_random_cleanse_cases','world_random_cleanse_native','portable_random_cleanse_contracts'),
            'burst1-ally':('portable_burst1_ally_cases','world_burst1_ally_native','portable_burst1_ally_contracts'),
            'skill-weapon-rosters':('portable_skill_weapon_roster_cases','world_skill_weapon_roster_native','portable_skill_weapon_roster_contracts'),
            'skill-weapon':('portable_skill_weapon_cases','world_skill_weapon_native','portable_skill_weapon_contracts'),
            'below-def':('portable_below_def_cases','world_below_def_native','portable_below_def_contracts'),
            'leftmost-rosters':('portable_leftmost_roster_cases','world_leftmost_roster_native','portable_leftmost_roster_contracts'),
            'leftmost':('portable_leftmost_cases','world_leftmost_native','portable_leftmost_contracts'),
            'duration-scaling-mixed':('portable_duration_scaling_extended_cases','world_duration_scaling_native','portable_duration_scaling_extended_contracts'),
            'duration-scaling':('portable_duration_scaling_cases','world_duration_scaling_native','portable_duration_scaling_contracts'),
            'not-core':('portable_not_core_cases','world_not_core_native','portable_not_core_contracts'),
            'partial-query':('portable_partial_query_cases','world_partial_query_native','portable_partial_query_contracts'),
            'nonfull-charge-reduction':('portable_partial_charge_reduction_cases','world_nonfull_charge_native','portable_nonfull_charge_contracts'),
            'nonfull-charge':('portable_nonfull_charge_cases','world_nonfull_charge_native','portable_nonfull_charge_contracts'),
            'squad-stage':('portable_squad_stage_cases','world_ally_burst_native','portable_squad_stage_contracts'),
            'aimed-enemy':('portable_aimed_enemy_cases','world_aimed_area_native','portable_aimed_enemy_contracts'),
            'aimed-rosters':('portable_aimed_roster_cases','world_aimed_roster_native','portable_aimed_roster_contracts'),
            'aimed-callback':('portable_aimed_callback_cases','world_aimed_area_native','portable_aimed_callback_contracts'),
            'aimed-area':('portable_aimed_area_cases','world_aimed_area_native','portable_aimed_area_contracts'),
            'aimed-packets':('portable_aimed_packet_cases','world_aimed_packet_native','portable_aimed_packet_contracts'),
            'interrupt-aim':('portable_interrupt_aim_cases','world_interrupt_aim_native','portable_interrupt_aim_contracts'),
            'mixed-query':('portable_mixed_query_cases','world_mixed_query_native','portable_mixed_query_contracts'),
            'late-attack-random':('portable_late_attack_random_cases','world_late_attack_random_native','portable_late_attack_random_contracts'),
            'state-predicates':('portable_state_predicate_cases','world_state_predicate_native','portable_state_predicate_contracts'),
            'ally-random':('portable_ally_random_reference_cases','world_ally_random_reference_native','portable_ally_random_reference_contracts'),
            'focus-aim':('portable_focus_aim_cases','world_focus_aim_native','portable_focus_aim_contracts'),
            'undying-predicate':('portable_undying_predicate_cases','world_undying_predicate_native','portable_undying_predicate_contracts'),
            'undying-predicate-rosters':('portable_undying_predicate_roster_cases','world_undying_predicate_roster_native','portable_undying_predicate_roster_contracts'),
            'accuracy-predicate-rosters':('portable_accuracy_predicate_roster_cases','world_accuracy_predicate_roster_native','portable_accuracy_predicate_roster_contracts'),
            'accuracy-predicate':('portable_accuracy_predicate_cases','world_accuracy_predicate_native','portable_accuracy_predicate_contracts'),
            'manual-swap-rosters':('portable_manual_swap_roster_cases','world_manual_swap_roster_native','portable_manual_swap_roster_contracts'),
            'manual-swap':('portable_manual_swap_cases','world_manual_swap_native','portable_manual_swap_contracts'),
            'ammo-equivalent':('portable_ammo_equivalent_cases','world_ammo_equivalent_native','portable_ammo_equivalent_contracts'),
            'ammo-equivalent-catalogue':('portable_ammo_equivalent_catalogue_cases','world_ammo_equivalent_native','portable_ammo_equivalent_contracts'),
            'ammo-equivalent-geometry':('portable_ammo_equivalent_geometry_cases','world_ammo_equivalent_native','portable_ammo_equivalent_contracts'),
            'pellet-shot':('portable_pellet_shot_cases','world_pellet_shot_native','portable_pellet_shot_contracts'),
            'lost-hp-attack-revival':('portable_lost_hp_attack_revival_cases','world_lost_hp_attack_native','portable_lost_hp_attack_contracts'),
            'lost-hp-attack':('portable_lost_hp_attack_cases','world_lost_hp_attack_native','portable_lost_hp_attack_contracts'),
            'skill-hp-basis-protection':('portable_skill_hp_basis_protection_cases','world_skill_hp_basis_native','portable_skill_hp_basis_contracts'),
            'skill-hp-basis':('portable_skill_hp_basis_cases','world_skill_hp_basis_native','portable_skill_hp_basis_contracts'),
            'mode-capacity':('portable_mode_capacity_cases','world_mode_capacity_native','portable_mode_capacity_contracts'),
            'ally-burst':('portable_ally_burst_cases','world_ally_burst_native','portable_ally_burst_contracts'),
            'revive':('portable_revive_cases','world_revive_native','portable_revive_contracts'),
            'entry-reload':('portable_entry_reload_cases','world_entry_reload_native','portable_entry_reload_contracts'),
            'heal-share':('portable_heal_share_cases','world_heal_share_native','portable_heal_share_contracts'),
            'heal-share-extended':('portable_heal_share_extra_cases','world_heal_share_native','portable_heal_share_contracts'),
            'heal-share-targets':('portable_heal_share_target_cases','world_heal_share_native','portable_heal_share_contracts'),
            'heal-share-lifesteal':('portable_heal_share_lifesteal_cases','world_heal_share_native','portable_heal_share_contracts'),
            'parts-skill':('portable_parts_skill_cases','world_parts_skill_native','portable_parts_skill_contracts'),
            'parts-skill-extended':('portable_parts_skill_extra_cases','world_parts_skill_native','portable_parts_skill_contracts'),
            'parts-skill-lifecycle':('portable_parts_skill_lifecycle_cases','world_parts_skill_native','portable_parts_skill_contracts')}
REFERENCES['destructible-modifier']=('destructible_modifier_cases','world_destructible_modifier_native','portable_destructible_modifier_contracts')
REFERENCES['destructible-shield-battle']=('destructible_shield_battle_cases','world_destructible_shield_battle_native','portable_destructible_shield_battle_contracts')
REFERENCES['destructible-hit-shield']=('destructible_hit_shield_cases','world_destructible_shield_battle_native','portable_destructible_hit_shield_contracts')
REFERENCES['destructible-weapon-shield']=('destructible_weapon_shield_cases','world_destructible_shield_battle_native','portable_destructible_weapon_shield_contracts')
REFERENCES['destructible-weapon-rosters']=('destructible_weapon_roster_cases','world_destructible_weapon_roster_native','portable_destructible_weapon_roster_contracts')
REFERENCES['destructible-skill-rosters']=('destructible_skill_roster_cases','world_destructible_weapon_roster_native','portable_destructible_skill_roster_contracts')
REFERENCES['attack-group-battle']=('portable_battle_attack_group_cases','world_battle_attack_group_native','portable_battle_attack_group_contracts')
REFERENCES['attack-group-native-route']=('portable_battle_native_route_cases','world_battle_native_route_native','portable_battle_native_route_contracts')
REFERENCES['attack-group-long']=('portable_long_group_cases','world_battle_native_route_native','portable_long_group_contracts')
REFERENCES['coordinate-skill']=('portable_coordinate_skill_cases','world_coordinate_skill_native','portable_coordinate_skill_contracts')
REFERENCES['coordinate-physical-common']=('portable_coordinate_physical_common_cases','world_coordinate_physical_common_reference','portable_coordinate_physical_common_contracts')
REFERENCES['coordinate-sampled-burst-common']=('portable_coordinate_sampled_burst_cases','world_coordinate_sampled_burst_native','portable_coordinate_sampled_burst_contracts')
REFERENCES['coordinate-sampled-vital-common']=('portable_coordinate_sampled_vital_cases','world_coordinate_sampled_vital_native','portable_coordinate_sampled_vital_contracts')
REFERENCES['coordinate-sampled-delivery-common']=('portable_coordinate_sampled_delivery_cases','world_coordinate_sampled_delivery_native','portable_coordinate_sampled_delivery_contracts')
REFERENCES['coordinate-sampled-skill-common']=('portable_coordinate_sampled_skill_cases','world_coordinate_sampled_skill_native','portable_coordinate_sampled_skill_contracts')
REFERENCES['coordinate-sampled-parent-common']=('portable_coordinate_sampled_parent_cases','world_coordinate_sampled_parent_native','portable_coordinate_sampling_contracts')
REFERENCES['coordinate-sampled-battle-common']=('portable_coordinate_sampled_battle_cases','world_coordinate_sampling_native','portable_coordinate_sampling_contracts')
REFERENCES['coordinate-sampling-common']=('portable_coordinate_sampling_cases','world_coordinate_sampling_native','portable_coordinate_sampling_contracts')
REFERENCES['coordinate-mixed-common']=('portable_coordinate_mixed_cases','world_coordinate_mixed_native','portable_coordinate_mixed_contracts')
REFERENCES['coordinate-group-common']=('portable_coordinate_group_cases','world_coordinate_group_native','portable_coordinate_group_contracts')
REFERENCES['coordinate-aim-common']=('portable_coordinate_aim_cases','world_coordinate_aim_native','portable_coordinate_aim_contracts')
REFERENCES['coordinate-typed-weapon-common']=('portable_coordinate_typed_weapon_cases','world_coordinate_typed_weapon_native','portable_coordinate_typed_weapon_contracts')
REFERENCES['logical-actor-geometry-common']=('portable_logical_geometry_cases','world_logical_geometry_native','portable_logical_geometry_contracts')
REFERENCES['logical-actor-rosters-common']=('portable_logical_geometry_roster_cases','world_logical_geometry_native','portable_logical_geometry_roster_contracts')
REFERENCES['enemy-healing-common']=('portable_enemy_healing_cases','world_enemy_healing_native','portable_enemy_healing_contracts')
REFERENCES['enemy-ammo-common']=('portable_enemy_ammo_cases','world_enemy_ammo_native','portable_enemy_ammo_contracts')
REFERENCES['add-self-destruct-native']=('world_add_self_destruct_native',)*3
REFERENCES['named-range-battle-common']=('portable_named_range_battle_cases','world_named_range_battle_native','portable_named_range_battle_contracts')
REFERENCES['coordinate-typed-owner-add-lifetime-common']=('portable_coordinate_typed_owner_add_lifetime_cases','world_coordinate_typed_owner_add_lifetime_native','portable_coordinate_typed_owner_add_lifetime_contracts')
REFERENCES['coordinate-typed-owner-hp-death-common']=('portable_coordinate_typed_owner_hp_death_cases','world_coordinate_typed_owner_hp_death_native','portable_coordinate_typed_owner_hp_death_contracts')
REFERENCES['heavyarms-target-count-native']=('portable_effect_target_count_cases','world_effect_target_count_native','portable_effect_target_count_contracts')
REFERENCES['heavyarms-lock-marker-native']=('portable_heavyarms_lock_cases','world_heavyarms_lock_native','portable_heavyarms_lock_contracts')
REFERENCES['physical-lock-cover-native']=('portable_physical_lock_cover_cases','world_physical_lock_cover_native','portable_physical_lock_cover_contracts')
REFERENCES['coordinate-typed-logical-owner-common']=('portable_coordinate_typed_logical_owner_cases','world_coordinate_typed_owner_native','portable_coordinate_typed_logical_owner_contracts')
REFERENCES['coordinate-typed-owner-common']=('portable_coordinate_typed_owner_cases','world_coordinate_typed_owner_native','portable_coordinate_typed_owner_contracts')
REFERENCES['coordinate-typed-owner-lifecycle-common']=('portable_coordinate_typed_owner_lifecycle_cases','world_coordinate_typed_owner_lifecycle_native','portable_coordinate_typed_owner_lifecycle_contracts')
REFERENCES['coordinate-typed-actor-common']=('portable_coordinate_typed_actor_cases','world_coordinate_typed_actor_native','portable_coordinate_typed_actor_contracts')
REFERENCES['coordinate-typed-aim-common']=('portable_coordinate_typed_aim_cases','world_coordinate_typed_aim_native','portable_coordinate_typed_aim_contracts')
REFERENCES['coordinate-accumulation-policy']=('portable_coordinate_accumulation_cases','world_coordinate_accumulation_native','portable_coordinate_accumulation_contracts')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def source_identity():
    paths=[ROOT/'app/portable_reference.py',ROOT/'scripts/nikke_gpu.py',ROOT/'app/engine_worker.py',ROOT/'app/engine_compat.py']
    # Native execution includes installed application compatibility layers (for
    # example weapon_mode_runtime), not only the upstream calculator files.
    paths += sorted((ROOT/'app').glob('*.py'))
    paths += sorted((ROOT/'research/upstream/nikke-calc-master/calculator').rglob('*.py'))
    # These native observers form one call chain. Include the literal factories
    # too, without importing or executing the rest of the research tree.
    paths += sorted((ROOT/'research').glob('world_*native.py'))
    paths += [ROOT/'research'/name for name in (
        'world_coordinate_physical_common.py',
        'world_coordinate_physical_common_reference.py', 'world_coordinate_matrix_common.py',
        'coordinate_landing_reference.py', 'coordinate_geometry_reference.py')]
    paths += [ROOT/'research'/name for name in ('portable_revive_cases.py','portable_revive_contracts.py','portable_persona_cases.py','portable_stun_cases.py','world_enemy_attack_cases.py','portable_burst_recipient_cases.py','portable_recipient_extension_cases.py','world_revive_native.py','enemy_target_native.py')]
    paths += sorted((ROOT/'research').glob('*cases.py'))
    paths += sorted((ROOT/'research').glob('portable_*contracts.py'))
    paths += sorted((ROOT/'research').glob('verify-world*.py'))
    paths += [ROOT/'research/verify-physical-locks.py']
    paths += sorted((ROOT/'scripts').glob('*cases.py'))
    paths += sorted((ROOT/'research/upstream/nikke-calc-master/data').rglob('*.json'))
    paths += sorted((ROOT/'data').glob('*.json'))
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}


def run_reference(suite,output,*,write,forbid_gpu):
    if suite not in REFERENCES:raise ValueError('Unknown native reference suite')
    output=Path(output)
    # Reserve before importing/running a case; failed evidence is never replaced.
    with output.open('x',encoding='utf-8') as stream:stream.write('{}\n')
    started=time.perf_counter()
    report=dict(schema=1,suite=suite,stage='cpu-native-contract',passed=False,cpu_reference_verified=False,calculation_verified=False,gpu_supported=False,gpu_calls=dict(build=0,execute=0),packing_calls=0,python=sys.version,platform=platform.platform(),cases=[],reference_model_gap_cases=0,positive_contract_cases=0,full_character_verified=0,full_goal_complete=False)
    if suite in ('coordinate-physical-common','coordinate-accumulation-policy','coordinate-aim-common','coordinate-group-common','coordinate-mixed-common','coordinate-sampling-common','coordinate-sampled-battle-common','coordinate-sampled-parent-common','coordinate-sampled-skill-common','coordinate-sampled-burst-common','coordinate-sampled-vital-common','coordinate-sampled-delivery-common'):
        report.update(stage='cpu-common-policy-contract',
                      reference_kind='deterministic-common-cpu',
                      numerical_contract='coordinate-landing-v1',
                      historical_native_equivalence=False)
        if suite in ('coordinate-sampling-common','coordinate-sampled-battle-common','coordinate-sampled-parent-common','coordinate-sampled-skill-common','coordinate-sampled-burst-common','coordinate-sampled-vital-common','coordinate-sampled-delivery-common'):report['numerical_contract']='coordinate-sample-v1 + coordinate-binary64-v1'
        if suite=='coordinate-aim-common':report['numerical_contract']='coordinate-landing-v1 + coordinate-area-matrix-common-v1'
    if suite in ('coordinate-typed-weapon-common','coordinate-typed-aim-common','coordinate-typed-actor-common','coordinate-typed-owner-common','coordinate-typed-owner-lifecycle-common','coordinate-typed-logical-owner-common','coordinate-typed-owner-add-lifetime-common','coordinate-typed-owner-hp-death-common'):
        report.update(stage='cpu-common-policy-contract',reference_kind='deterministic-common-cpu',
                      numerical_contract='coordinate-sample-v1 + coordinate-binary64-v1 + declared-typed-geometry-v1',
                      historical_native_equivalence=False,in_game_rules_verified=False)
        if suite=='coordinate-typed-aim-common':report.update(declared_aim_policy='typed-before-body-v1',gpu_wire_connected=False)
        if suite=='coordinate-typed-actor-common':report.update(declared_actor_policy='canonical-current-damage-v1',enemy_field_ownership_connected=False)
        if suite in ('coordinate-typed-logical-owner-common','coordinate-typed-owner-add-lifetime-common','coordinate-typed-owner-hp-death-common'):report.update(declared_actor_policy='logical-owned-current-fields-v1',gpu_wire_connected=False)
        if suite in ('coordinate-typed-owner-common','coordinate-typed-owner-lifecycle-common'):report.update(declared_actor_policy='body-owned-current-fields-v1',gpu_wire_connected=False)
    if suite in ('logical-actor-geometry-common','logical-actor-rosters-common'):
        report.update(stage='cpu-common-policy-contract',reference_kind='declared-logical-actor-geometry-cpu',
            numerical_contract='coordinate-sample-v1 + coordinate-binary64-v1 + declared-logical-actor-colliders-v1',
            historical_native_equivalence=False,in_game_rules_verified=False,gpu_wire_connected=False)
    if suite=='named-range-battle-common':
        report.update(stage='cpu-common-policy-contract',reference_kind='declared-named-radial-original-battle',historical_native_equivalence=False,in_game_rules_verified=False,gpu_wire_connected=False)
    if suite=='enemy-healing-common':
        report.update(stage='cpu-common-policy-contract',reference_kind='declared-source-node-enemy-healing-cpu',
            historical_native_equivalence=False,in_game_rules_verified=False,gpu_wire_connected=False)
    if suite=='enemy-ammo-common':
        report.update(stage='cpu-common-policy-contract',reference_kind='declared-enemy-magazine-attempt-v1',
            historical_native_equivalence=False,in_game_rules_verified=False,gpu_wire_connected=False,
            capacity_model='fixed-declared',source_schedule_policy='retain original scheduled attempts; never retime blocked attempts')
    if suite=='add-self-destruct-native':
        report.update(stage='cpu-native-component-contract',reference_kind='canonical-add-final-shot-retirement',
            full_battle_validation=False,gpu_wire_connected=False,in_game_rules_verified=False)
    try:
        # Legacy native comparators contain assertions. Reject before importing
        # or running them; optimized Python must never certify those contracts.
        if sys.flags.optimize:
            raise RuntimeError('Native reference requires assertions enabled; optimized Python is forbidden')
        sources=source_identity();report['source_sha256']=sources
        import portable_runtime,portable_backend,detail_gpu
        def no_packing(*args,**kw):raise RuntimeError('Portable packing forbidden in native contract stage')
        # Install guards before imports: aliases imported by adapters inherit them.
        with forbid_gpu(),patch.object(portable_runtime,'compile_program',no_packing),patch.object(detail_gpu,'compile_effects',no_packing),patch.object(detail_gpu,'compile_full',no_packing),patch.object(portable_runtime,'execute',portable_backend.execute),patch.object(portable_runtime,'execute_batches',portable_backend.execute_batches):
            factories,natives,contracts=[importlib.import_module(name) for name in REFERENCES[suite]]
            cases=factories.fixtures();before=copy.deepcopy(cases)
            if not cases or len({c['name'] for c in cases})!=len(cases):raise ValueError('Empty or duplicate native contracts')
            for case in cases:
                report['current_case']=case['name']
                input_hash=digest(case)
                native,trace=natives.observe(case)
                contract=contracts.verify(case,native)
                report['cases'].append(dict(name=case['name'],input_sha256=input_hash,native_sha256=digest(native),trace_sha256=digest(trace),contract=contract,native=native))
                if contract.get('verified') is not True:raise ValueError('Native contract not verified: '+case['name'])
                if contract.get('reference_model_gap') is True:report['reference_model_gap_cases']+=1
                else:report['positive_contract_cases']+=1
            if cases!=before:raise ValueError('Native observation changed literal inputs')
        if source_identity()!=sources:raise ValueError('Native reference sources changed during execution')
        from portable_typed_cuda_proof_audit import verify_cpu_gpu_calls
        verify_cpu_gpu_calls(report['gpu_calls'])
        report.update(passed=True,cpu_reference_verified=True,case_count=len(cases))
        report.pop('current_case',None)
    except BaseException as error:
        report['error']=type(error).__name__+': '+str(error)
        raise
    finally:
        report['elapsed_seconds']=time.perf_counter()-started
        write(output,report)
    return {k:report[k] for k in ('suite','stage','passed','cpu_reference_verified','calculation_verified','gpu_supported','case_count','positive_contract_cases','reference_model_gap_cases','gpu_calls','packing_calls','elapsed_seconds')}
