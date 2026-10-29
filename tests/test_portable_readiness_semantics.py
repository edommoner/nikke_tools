"""Route real blockers without inventing a consumer, support or unlock claim."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_readiness_semantics import reference_readiness,work_lanes
from portable_readiness import issue,summarize


class ReadinessSemanticsTests(unittest.TestCase):
    def test_pinned_storage_proofs_keep_historical_and_joined_scopes_separate(self):
        from portable_model_gap_audit import verify
        audit=verify(ROOT)
        expected=audit['coordinate_world']['numeric_frontend']['resident_storage_validation']
        for stat in ('projectile_dmg_pct','shield_dmg_pct'):
            result=reference_readiness(self.blocker(stat));proof=result['resident_storage_validation']
            self.assertEqual(proof,expected)
            frame=proof['frames'];append=proof['appends']
            for record in (frame,append):
                raw=(ROOT/record['evidence']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),record['evidence_sha256'])
                self.assertFalse(record['public_admission']);self.assertFalse(record['full_character_verified'])
            metal=json.loads((ROOT/frame['evidence']).read_bytes());cuda=json.loads((ROOT/append['evidence']).read_bytes())
            self.assertTrue(metal['calculation_verified']);self.assertTrue(metal['old_entry_input_output_native_fingerprints_preserved'])
            self.assertEqual((frame['inputs'],frame['native_cases']),(metal['independent_audit']['input_count'],metal['independent_audit']['native_cases']))
            self.assertEqual([i for g in metal['independent_audit']['groups'] for i in g['case_indices']],list(range(106)))
            self.assertFalse(frame['cuda_device_verified'])
            self.assertEqual(append['inputs'],cuda['input_count']);self.assertEqual(append['canonical_battle_cases'],0)
            self.assertTrue(cuda['calculation_verified']);self.assertTrue(cuda['all_entry_input_output_native_fingerprints_identical'])
            self.assertTrue(append['metal_cuda_fingerprints_equal']);self.assertTrue(append['cuda_calculation_verified'])
            self.assertTrue(cuda['windows']['generation_cache']['hit']);self.assertTrue(cuda['windows']['cuda_cache']['hit'])
            for name in ('nvrtc_calls','slang_compiler_calls'):self.assertEqual(cuda['windows'][name],0)
            self.assertFalse(cuda['windows']['passed']);self.assertFalse(cuda['windows']['preservation_verified'])
            self.assertFalse(append['overall_stage_passed']);self.assertFalse(append['environment_preservation_verified'])
            self.assertFalse(append['full_resident_battle_verified']);self.assertFalse(result['gpu_supported'])
            self.assertEqual(result['lane'],'reference_model_gap');self.assertFalse(audit['full_goal_complete'])
            wire=proof['wire'];raw=(ROOT/wire['evidence']).read_bytes();peer=json.loads(raw)
            self.assertEqual(wire['evidence_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(wire['inputs'],peer['input_count']);self.assertEqual(wire['native_reference_cases'],peer['native_reference_cases'])
            self.assertTrue(peer['gpu_protocol_verified']);self.assertTrue(wire['cuda_device_execution_verified'])
            self.assertTrue(peer['shared_metal_wire_equivalence_verified']);self.assertTrue(wire['shared_metal_wire_equivalence_verified'])
            self.assertEqual((peer['launch_calls'],peer['sync_calls'],peer['readback_calls']),(7,7,106))
            for name in ('calculation_verified','overall_stage_passed','public_admission','full_character_verified'):self.assertFalse(wire[name])
            self.assertTrue(wire['pending_independent_native_audit']);self.assertFalse(wire['original_cuda_raw_independently_read_on_mac'])
            joined=proof['joined'];raw=(ROOT/joined['evidence']).read_bytes();report=json.loads(raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),joined['evidence_sha256'])
            self.assertEqual((joined['inputs'],joined['native_cases'],joined['rejected_cases']),(106,63,43))
            self.assertTrue(joined['calculation_verified']);self.assertTrue(report['calculation_verified'])
            self.assertEqual(joined['independent_native_groups'],report['independent_native_groups'])
            for key in ('source_host_cuda_envelope_independently_audited','cuda_envelope_received_as_peer_summary','metal_witness_native_independently_verified'):self.assertTrue(joined[key]);self.assertTrue(report[key])
            self.assertFalse(joined['original_cuda_raw_read_on_mac']);self.assertFalse(report['original_cuda_raw_read_on_mac'])
            for key in ('environment_preservation_verified','overall_stage_passed','public_admission','full_character_verified'):self.assertFalse(joined[key])
            self.assertFalse(result['gpu_supported']);self.assertFalse(audit['full_goal_complete'])

    def test_enemy_ammo_has_shared_math_but_requires_enemy_state_and_real_producers(self):
        from portable_model_gap_audit import verify
        r=reference_readiness(dict(phase='effect',kind='instant',stat='ammo_charge_pct',target='all_enemies'))
        p=r['enemy_ammo_prerequisites']
        self.assertEqual(p,verify(ROOT)['enemy_ammo']['prerequisites'])
        self.assertIn('ties-to-even',p['rounding']);self.assertIn('empty loop',p['named_completion'])
        self.assertIn('enemy shot consumption',p['required_producers'])
        for key in ('enemy_state_defined','enemy_instant_connected','enemy_shot_reload_connected','original_profile_gpu_verified','default_producer_installed'):
            self.assertFalse(p[key])
        self.assertEqual(r['lane'],'reference_model_gap');self.assertFalse(r['gpu_supported'])
        declared=p['declared_cpu_contract']
        self.assertEqual(declared,verify(ROOT)['enemy_ammo']['declared_source_contract'])
        self.assertEqual((declared['suite'],declared['cases'],declared['original_definitions']),('enemy-ammo-common',6,76))
        self.assertEqual(declared['capacity_model'],'fixed-declared')
        self.assertTrue(declared['original_operator_code_reused'])
        for key in ('gpu_wire_connected','metal_verified','cuda_verified','default_path_installed'):self.assertFalse(declared[key])
    def test_movement_duration_states_keep_spatial_dependencies_explicit(self):
        for stat in ('enemy_movement_disable','force_move'):
            r=reference_readiness(dict(phase='effect',kind='buff',stat=stat,target='enemies_in_range'))
            p=r['movement_prerequisites'];self.assertEqual(p['operator_model'],'duration state')
            self.assertFalse(p['numeric_magnitude_consumer_required']);self.assertTrue(p['duration_carrier_required'])
            self.assertTrue(p['world_position_provider_required']);self.assertTrue(p['spatial_recipient_model_required'])
            self.assertEqual(p['force_destination_and_motion_policy_required'],stat=='force_move')
            self.assertFalse(p['current_world_consumer_verified']);self.assertFalse(r['gpu_supported'])
            from portable_model_gap_audit import verify
            declared=p['declared_cpu_contract']
            self.assertEqual(declared,verify(ROOT)['missing_stats'][stat]['declared_movement_contract'])
            self.assertEqual((declared['suite'],declared['cases']),('enemy-movement-common',5))
            self.assertTrue(declared['existing_duration_carriers']);self.assertTrue(declared['existing_shot_landing_damage'])
            self.assertTrue(declared['gpu_world_consumer_connected'])
            for key in ('actual_spatial_recipient_selection_verified','in_game_motion_policy_verified','default_producer_installed'):self.assertFalse(declared[key])
            math_proof=declared['declared_math_validation'];raw=(ROOT/math_proof['evidence']).read_bytes();evidence=json.loads(raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),math_proof['evidence_sha256'])
            self.assertEqual((math_proof['inputs'],math_proof['native_cases'],math_proof['rejected_cases']),(43,34,9))
            self.assertTrue(evidence['math_calculation_verified']);self.assertTrue(evidence['independent_audit']['calculation_verified'])
            self.assertEqual(evidence['gpu_execution_count'],1);self.assertEqual(evidence['gpu_calls_during_replay_and_seal'],0)
            self.assertFalse(evidence['gpu_world_consumer_connected']);self.assertFalse(evidence['full_character_verified'])
            battle=declared['declared_battle_validation'];raw=(ROOT/battle['evidence']).read_bytes();proof=json.loads(raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),battle['evidence_sha256'])
            self.assertEqual((proof['inputs'],proof['native_cases'],proof['rejected_cases']),(15,5,10))
            golden=json.loads((ROOT/'research/portable-enemy-movement-battle-v1-expected.json').read_text())
            for key in ('source_sha256','generated_normalized','input_sha256','output_sha256'):self.assertEqual(proof[key],golden[key])
            independent=proof['independent_audit'];self.assertTrue(independent['calculation_verified'])
            self.assertEqual([i for group in independent['groups'] for i in group['case_indices']],list(range(15)))
            self.assertFalse(independent['live_parent_receipt_present']);self.assertEqual(independent['gpu_calls'],0)
            self.assertTrue(all(group['elapsed_seconds']<=180 for group in independent['groups']))
            self.assertTrue(proof['gpu_world_consumer_connected']);self.assertTrue(proof['declared_battle_calculation_verified'])
            for key in ('cuda_verified','actual_spatial_recipient_selection_verified','in_game_motion_policy_verified','default_producer_installed','full_character_verified','full_goal_complete'):self.assertFalse(proof[key])
    def test_resident_frame_seal_keeps_missing_reference_and_cuda_gates_closed(self):
        raw=(ROOT/'tests/fixtures/resident-frames-independent-v2.json').read_bytes();audit=json.loads(raw)
        for stat in ('projectile_dmg_pct','shield_dmg_pct'):
            result=reference_readiness(self.blocker(stat));frame=result['resident_frames_validation']
            self.assertEqual(frame['evidence_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual((frame['inputs'],frame['native_cases']),(audit['input_count'],audit['native_cases']))
            self.assertEqual([i for g in audit['groups'] for i in g['case_indices']],list(range(106)))
            self.assertTrue(all(g['elapsed_seconds']<=audit['per_group_timeout_seconds'] for g in audit['groups']))
            self.assertTrue(audit['certificate_from_same_audit']);self.assertEqual(audit['gpu_calls'],0);self.assertFalse(audit['live_parent_receipt_present'])
            self.assertTrue(frame['metal_verified']);self.assertTrue(frame['independently_audited'])
            self.assertEqual((frame['frame_slots'],frame['extra_runtime_bytes']),(32,4096))
            for key in ('cuda_device_verified','cuda_physical_stack_reduction_verified','canonical_consumer_verified','full_character_verified'):self.assertIs(frame[key],False)
            self.assertEqual(result['lane'],'reference_model_gap');self.assertFalse(result['gpu_supported'])
    def test_resident_and_standalone_cuda_evidence_keep_distinct_support_scopes(self):
        independent=(ROOT/'tests/fixtures/resident-arc-independent-v2.json').read_bytes()
        comparison=(ROOT/'tests/fixtures/landing-arc-cuda-comparison-v4.json').read_bytes()
        transport=(ROOT/'tests/fixtures/landing-arc-cuda-summary-v4.json').read_bytes()
        metal=json.loads(independent);cuda=json.loads(comparison);summary=json.loads(transport)
        for stat in ('projectile_dmg_pct','shield_dmg_pct'):
            r=reference_readiness(self.blocker(stat));m=r['resident_arc_validation'];c=r['standalone_landing_cuda_validation']
            self.assertEqual(m['evidence_sha256'],hashlib.sha256(independent).hexdigest())
            self.assertEqual((m['inputs'],m['native_cases']),(metal['input_count'],metal['native_cases']))
            self.assertTrue(metal['calculation_verified']);self.assertTrue(m['metal_verified']);self.assertFalse(m['cuda_device_verified'])
            self.assertEqual(c['evidence_sha256'],hashlib.sha256(comparison).hexdigest())
            self.assertEqual(c['transport_evidence_sha256'],hashlib.sha256(transport).hexdigest())
            self.assertEqual((c['inputs'],c['native_cases']),(cuda['input_count'],cuda['native_oracles']))
            self.assertTrue(cuda['calculation_verified']);self.assertEqual(cuda['mismatches'],[])
            self.assertEqual(c['nvrtc_calls'],summary['actions']['nvrtc_calls'])
            self.assertEqual(c['compiler_library_requests'],summary['compiler_library_requests'])
            self.assertEqual(c['required_cubin_cache_hit'],summary['actual_cache']['hit'])
            returned={r['stage']:r['return_code'] for r in summary['gpu_api_returns'] if r['state']=='returned'}
            self.assertTrue(c['launch_sync_readback_verified']);self.assertEqual([returned[s] for s in ('cuLaunchKernel','cuCtxSynchronize','cuMemcpyDtoH_v2')],[0,0,0])
            self.assertEqual(c['overall_stage_passed'],summary['result']['passed'])
            self.assertFalse(c['full_resident_battle_verified']);self.assertFalse(c['overall_stage_passed'])
            self.assertEqual(r['lane'],'reference_model_gap');self.assertFalse(r['gpu_supported']);self.assertFalse(r['full_character_verified'])

    def test_ammo_equivalent_has_native_contracts_but_no_admission_claim(self):
        row=dict(phase='effect',category='effect',kind='instant',stat='squad_ammo_consume_as',target='self',scaling=None)
        result=reference_readiness(row)
        self.assertEqual(result['lane'],'gpu_lowering_candidate');self.assertEqual(result['native_consumer'],'confirmed_source')
        self.assertEqual(result['recorded_cases'],25);self.assertEqual(result['reference_suites'],['ammo-equivalent'])
        for key in ('gpu_supported','gpu_admission_verified','full_character_verified','runtime_validation_performed'):self.assertIs(result[key],False)
        for changed in (dict(target='all_allies'),dict(scaling='stack_count'),dict(fields=['future']),dict(category='fields')):
            with self.subTest(changed=changed):self.assertEqual(reference_readiness(dict(row,**changed))['lane'],'native_contract_extension')
        for changed in (dict(phase='program'),dict(kind='buff'),dict(stat='unproven')):
            with self.subTest(changed=changed):self.assertEqual(reference_readiness(dict(row,**changed))['lane'],'reference_review')

    def test_ammo_equivalent_recorded_count_matches_registered_literals(self):
        sys.path.insert(0,str(ROOT/'research'))
        try:
            from portable_reference import REFERENCES
            import importlib
            result=reference_readiness(dict(phase='effect',category='effect',kind='instant',stat='squad_ammo_consume_as',target='self'))
            cases=[c for suite in result['reference_suites'] for c in importlib.import_module(REFERENCES[suite][0]).fixtures()]
            self.assertEqual(len(cases),result['recorded_cases']);self.assertEqual(len({c['name'] for c in cases}),len(cases))
        finally:sys.path.pop(0)

    def blocker(self,stat,**kw):
        effect=dict(type='buff',stat=stat,target='all_allies',**kw)
        return issue(ValueError('Unported buff stat'),effect)

    def test_declared_model_is_a_subset_prerequisite_and_never_gpu_support(self):
        result=reference_readiness(self.blocker('heal_split'))
        self.assertEqual(result['lane'],'gpu_lowering_candidate');self.assertEqual(result['recorded_cases'],43)
        self.assertEqual(result['reference_suites'],['heal-share','heal-share-extended','heal-share-targets','heal-share-lifesteal'])
        for key in ('gpu_supported','gpu_admission_verified','full_character_verified','runtime_validation_performed'):self.assertIs(result[key],False)

    def test_recorded_heal_contract_count_matches_the_registered_literal_suites(self):
        sys.path.insert(0,str(ROOT/'research'))
        try:
            from portable_reference import REFERENCES
            import importlib
            suites=reference_readiness(self.blocker('heal_split'))['reference_suites']
            cases=[case for suite in suites for case in importlib.import_module(REFERENCES[suite][0]).fixtures()]
            self.assertEqual(len({case['name'] for case in cases}),len(cases))
            self.assertEqual(reference_readiness(self.blocker('heal_split'))['recorded_cases'],len(cases))
        finally:sys.path.pop(0)

    def test_unknown_target_scaling_field_or_program_requires_more_native_contracts(self):
        base=self.blocker('heal_split')
        for extra in (dict(target='boss'),dict(scaling='unproven'),dict(fields=['future']),dict(category='fields')):
            with self.subTest(extra=extra):self.assertEqual(reference_readiness(dict(base,**extra))['lane'],'native_contract_extension')
        self.assertEqual(reference_readiness(dict(base,phase='program'))['lane'],'reference_review')

    def test_confirmed_missing_target_world_is_never_noop_support(self):
        for stat in ('projectile_dmg_pct','shield_dmg_pct'):
            r=reference_readiness(self.blocker(stat));self.assertEqual(r['lane'],'reference_model_gap');self.assertEqual(r['native_consumer'],'explicitly_missing_target_world')
            self.assertFalse(r['gpu_supported']);self.assertFalse(r['gpu_admission_verified'])
            self.assertEqual(r['typed_foundation_validation']['inputs'],18)
            self.assertFalse(r['typed_foundation_validation']['battle_producers_verified'])
            self.assertFalse(r['gpu_supported']);self.assertFalse(r['runtime_validation_performed'])

    def test_original_modifier_probe_is_bounded_and_keeps_the_reference_gap(self):
        for stat,count in [('projectile_dmg_pct',10),('shield_dmg_pct',9)]:
            r=reference_readiness(self.blocker(stat));v=r['typed_original_modifier_validation']
            self.assertEqual((v['inputs'],v['native_cases'],v['axis_cases']),(19,19,count))
            self.assertEqual(r['lane'],'reference_model_gap');self.assertFalse(r['gpu_supported'])
            self.assertTrue(v['metal_verified']);self.assertTrue(v['independently_audited']);self.assertTrue(v['explicit_added_damage_probe'])
            for key in ('automatic_weapon_aim_verified','coordinates_verified','canonical_consumer_verified','cuda_device_verified','full_character_verified'):self.assertFalse(v[key])

    def test_coordinate_typed_modifier_proof_does_not_admit_automatic_aim(self):
        for stat,count in [('projectile_dmg_pct',4),('shield_dmg_pct',5)]:
            r=reference_readiness(self.blocker(stat));v=r['typed_coordinate_modifier_validation']
            self.assertEqual((v['inputs'],v['axis_cases']),(10,count));self.assertTrue(v['coordinate_battle_connected']);self.assertTrue(v['shared_sampled_rng'])
            self.assertFalse(v['automatic_typed_weapon_aim_verified']);self.assertFalse(v['cuda_device_verified']);self.assertFalse(r['gpu_supported']);self.assertEqual(r['lane'],'reference_model_gap')
            spatial=r['typed_spatial_modifier_validation']
            self.assertEqual((spatial['inputs'],spatial['native_cases'],spatial['added_spatial_cases']),(28,18,8))
            self.assertTrue(spatial['live_world_generation_selection']);self.assertTrue(spatial['explicit_point_and_extra_attack'])
            for key in ('automatic_typed_weapon_aim_verified','canonical_consumer_verified','cuda_device_verified','in_game_rules_verified','full_character_verified'):self.assertFalse(spatial[key])
            live=r['typed_live_aim_validation'];self.assertEqual((live['inputs'],live['native_cases'],live['added_live_aim_cases']),(35,22,4))
            self.assertTrue(live['canonical_aim_bank_consumer_verified']);self.assertTrue(live['previous_frame_skill_aim_verified'])
            for key in ('automatic_typed_weapon_aim_verified','canonical_consumer_verified','cuda_device_verified','in_game_rules_verified','full_character_verified'):self.assertFalse(live[key])

    def test_parts_field_has_a_source_but_never_invented_runtime_coverage(self):
        row=dict(phase='effect',kind='damage',category='fields',fields=['hits_parts'])
        result=reference_readiness(row)
        self.assertEqual(result['lane'],'native_contract_extension');self.assertEqual(result['native_consumer'],'confirmed_source')
        self.assertEqual(result['recorded_cases'],32);self.assertEqual(result['reference_suites'],['parts-skill','parts-skill-extended','parts-skill-lifecycle'])
        self.assertEqual(result['reference_model_gap_cases'],1)
        self.assertFalse(result['gpu_supported']);self.assertFalse(result['runtime_validation_performed'])
        self.assertEqual(reference_readiness(dict(row,fields=['hits_parts','scaling']))['lane'],'reference_review')
        self.assertEqual(reference_readiness(dict(row,kind='buff'))['lane'],'reference_review')

    def test_projectile_definition_bridge_is_scoped_and_does_not_admit_battle(self):
        row=dict(phase='effect',kind='damage',stat='damage',target='all_projectiles')
        result=reference_readiness(row);self.assertEqual(result['lane'],'reference_model_gap')
        v=result['typed_skill_validation'];self.assertEqual((v['inputs'],v['native_cases'],v['original_definitions']),(18,10,1))
        self.assertTrue(v['metal_verified']);self.assertFalse(v['automatic_battle_dispatch_verified']);self.assertFalse(v['projectile_modifiers_verified'])
        self.assertFalse(result['gpu_supported']);self.assertFalse(result['gpu_admission_verified']);self.assertFalse(result['full_character_verified'])
        frame=result['typed_frame_validation'];self.assertEqual((frame['inputs'],frame['native_cases']),(26,17));self.assertTrue(frame['ordinary_notify_and_budget_verified']);self.assertFalse(frame['full_battle_scheduler_verified'])
        original=result['typed_original_battle_validation'];self.assertEqual((original['inputs'],original['native_cases'],original['original_definitions']),(8,8,1));self.assertEqual(original['skill_levels'],[1,5,10]);self.assertTrue(original['actual_burst_notification_verified']);self.assertFalse(original['original_full_profile_verified']);self.assertFalse(original['cuda_device_verified'])
        battle=result['typed_battle_validation'];self.assertEqual((battle['inputs'],battle['native_cases']),(44,31));self.assertTrue(battle['actual_battle_scheduler_verified']);self.assertTrue(battle['ordinary_cleared_nodes_coexist']);self.assertTrue(battle['nested_same_producer_reentry_verified']);self.assertTrue(battle['explicit_boss_and_generic_child_recipients_verified']);self.assertFalse(battle['typed_logical_enemy_policy_verified']);self.assertFalse(battle['separate_cpu_event_list']);self.assertFalse(battle['canonical_targets_cleared_verified']);self.assertFalse(battle['original_full_profile_verified'])

    def test_declared_modifier_design_does_not_promote_model_gap_or_gpu_support(self):
        for stat in ('projectile_dmg_pct','shield_dmg_pct'):
            r=reference_readiness(self.blocker(stat));self.assertEqual(r['lane'],'reference_model_gap')
            v=r['typed_modifier_design'];self.assertEqual(v['cases'],20);self.assertTrue(v['cpu_contract_verified'])
            self.assertTrue(v['metal_verified']);self.assertEqual((v['metal_inputs'],v['metal_native_cases']),(29,20))
            for field in ('canonical_consumer_verified','cuda_device_verified','battle_connected','in_game_rules_verified'):self.assertFalse(v[field])
            self.assertFalse(r['gpu_supported']);self.assertFalse(r['runtime_validation_performed'])

    def test_projectile_battle_metadata_does_not_certify_hp_shield_or_public_admission(self):
        for issue in (self.blocker('projectile_dmg_pct'),dict(phase='effect',kind='damage',stat='damage',target='all_projectiles')):
            r=reference_readiness(issue);v=r['typed_modifier_battle_validation'];self.assertEqual((v['inputs'],v['native_cases']),(18,12));self.assertTrue(v['actual_scheduler_verified']);self.assertTrue(v['parent_damage_frozen']);self.assertTrue(v['named_coefficient_observed'])
            for flag in ('hp_shield_battle_verified','cuda_device_verified','in_game_rules_verified','original_full_profile_verified'):self.assertFalse(v[flag])
            self.assertFalse(r['gpu_supported']);self.assertEqual(r['lane'],'reference_model_gap')
        self.assertNotIn('typed_modifier_battle_validation',reference_readiness(self.blocker('shield_dmg_pct')))

    def test_hp_shield_plain_skill_proof_does_not_enable_general_admission(self):
        r=reference_readiness(self.blocker('shield_dmg_pct'));v=r['typed_shield_battle_validation']
        self.assertEqual((v['inputs'],v['native_cases'],v['rejected_cases'],v['new_shield_cases']),(88,58,30,15))
        for flag in ('metal_verified','independently_audited','same_frame_stack','explicit_boss_owner_generation','no_overflow','body_fallback','death_counter_children'):self.assertTrue(v[flag])
        for flag in ('weapon_interception_verified','hit_shield_interception_verified','piercing_interception_verified','cuda_device_verified','in_game_rules_verified','original_full_profile_verified'):self.assertFalse(v[flag])
        self.assertEqual(r['lane'],'reference_model_gap');self.assertFalse(r['gpu_supported']);self.assertFalse(r['gpu_admission_verified'])

    def test_hit_credit_proof_remains_plain_skill_and_model_gap(self):
        r=reference_readiness(self.blocker('shield_dmg_pct'));v=r['typed_hit_shield_battle_validation']
        self.assertEqual((v['inputs'],v['native_cases'],v['rejected_cases'],v['new_credit_cases']),(111,76,35,18))
        for flag in ('metal_verified','independently_audited','same_frame_stack','damage_and_credit_independent','plain_skill_hit_shield_interception_verified','prior88_all_input_native_and_raw_retained'):self.assertTrue(v[flag])
        for flag in ('weapon_interception_verified','piercing_interception_verified','cuda_device_verified','in_game_rules_verified','original_full_profile_verified'):self.assertFalse(v[flag])
        self.assertEqual(r['lane'],'reference_model_gap');self.assertFalse(r['gpu_supported']);self.assertFalse(r['gpu_admission_verified'])

    def test_weapon_shield_proof_does_not_certify_geometry_or_public_admission(self):
        r=reference_readiness(self.blocker('shield_dmg_pct'));v=r['typed_weapon_shield_battle_validation']
        self.assertEqual((v['inputs'],v['native_cases'],v['rejected_cases'],v['new_weapon_cases']),(141,98,43,22))
        for flag in ('metal_verified','independently_audited','shot_factors_frozen','per_pellet_live_selection','hp_hit_body_continuation','auto_charge_tap_modes_muzzles_verified','ammo_and_gauge_verified','prior111_all_input_native_and_raw_retained'):self.assertTrue(v[flag])
        for flag in ('coordinates_verified','parts_verified','piercing_interception_verified','lifesteal_accumulation_verified','add_owner_verified','cuda_device_verified','in_game_rules_verified','original_full_profile_verified'):self.assertFalse(v[flag])
        self.assertEqual(r['lane'],'reference_model_gap');self.assertFalse(r['gpu_supported']);self.assertFalse(r['gpu_admission_verified'])
        self.assertNotIn('typed_weapon_shield_battle_validation',reference_readiness(self.blocker('projectile_dmg_pct')))

    def test_inert_model_gap_is_checked_against_current_canonical_classification(self):
        r=reference_readiness(self.blocker('cover_def_pct'));self.assertEqual(r['lane'],'reference_model_gap')
        import effect_spec
        from unittest.mock import patch
        with patch.object(effect_spec,'SCOPED_INERT',frozenset()):self.assertEqual(reference_readiness(self.blocker('cover_def_pct'))['lane'],'reference_review')

    def test_every_priority_has_exactly_one_lane_and_original_grouping_is_unchanged(self):
        issues=[self.blocker(stat) for stat in ('projectile_dmg_pct','heal_split','shield_dmg_pct','cover_def_pct','unknown')]
        rows=[dict(character=str(i),favorite_stage=0,effect_blockers=[dict(issue=entry)]) for i,entry in enumerate(issues)]
        before=copy.deepcopy(rows);priorities=summarize(rows);lanes=work_lanes(priorities)
        self.assertEqual(rows,before);self.assertEqual(sorted(i for values in lanes.values() for i in values),list(range(5)))
        self.assertEqual({r['issue']['code'] for r in priorities},{i['code'] for i in issues})
        self.assertTrue(all(r['affected_profiles']==r['single_observed_category_profiles']==r['blocked_definitions']==1 for r in priorities))

    def test_annotation_does_not_admit_the_previously_rejected_effect(self):
        from portable_runtime import validate_effect,UnsupportedPortable
        effect=dict(type='buff',stat='unknown_heal_split',fixed_value=1,target='all_allies',duration=-1,trigger=dict(timing=['battle_start'],condition=[]))
        before=copy.deepcopy(effect)
        with self.assertRaises(UnsupportedPortable):validate_effect(effect,combat={},world_frame=True)
        reference_readiness(self.blocker('heal_split'))
        with self.assertRaises(UnsupportedPortable):validate_effect(effect,combat={},world_frame=True)
        self.assertEqual(effect,before)


if __name__=='__main__':unittest.main()

class PartsInventoryCountTests(unittest.TestCase):
    def test_declared_count_and_gaps_match_registered_literal_contracts(self):
        sys.path.insert(0,str(ROOT/'research'))
        try:
            import importlib
            from portable_reference import REFERENCES
            result=reference_readiness(dict(phase='effect',kind='damage',fields=['hits_parts']))
            cases=[c for suite in result['reference_suites'] for c in importlib.import_module(REFERENCES[suite][0]).fixtures()]
            self.assertEqual(len({c['name'] for c in cases}),len(cases))
            self.assertEqual(len(cases),result['recorded_cases'])
            self.assertEqual(sum(bool(c['contract'].get('reference_model_gap')) for c in cases),result['reference_model_gap_cases'])
        finally:sys.path.pop(0)


class LockOnReadinessTests(unittest.TestCase):
 def test_generic_marker_evidence_does_not_promote_spatial_or_gpu_support(self):
  from portable_readiness_semantics import reference_readiness
  r=reference_readiness(dict(phase='effect',kind='buff',stat='lock_on',target='enemies_nearest:1'))
  self.assertEqual(r['lane'],'reference_model_gap');self.assertEqual(r['contract_coverage'],'native_named_marker_only')
  self.assertFalse(r['gpu_supported']);self.assertFalse(r['gpu_admission_verified'])
  marker=r['native_marker_contract'];self.assertTrue(marker['carrier_stack_remove_and_named_query']);self.assertEqual(marker['original_definitions'],25)
  self.assertFalse(marker['spatial_selection_verified']);self.assertFalse(marker['target_count_extension_verified']);self.assertFalse(marker['full_original_typed_projectile_verified'])
