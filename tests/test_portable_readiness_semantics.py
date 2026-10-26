"""Route real blockers without inventing a consumer, support or unlock claim."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_readiness_semantics import reference_readiness,work_lanes
from portable_readiness import issue,summarize


class ReadinessSemanticsTests(unittest.TestCase):
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
