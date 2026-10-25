"""The source frontier and passive oracle must not imply GPU coverage."""
import importlib.util
import sys
import tempfile
import contextlib
import io
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app', 'research')]
from portable_coordinate_frontier import verify


class FrontierTests(unittest.TestCase):
    def test_audit_reuses_public_and_arena_guards_without_battles(self):
        result = verify(ROOT)
        self.assertTrue(result['passed'])
        self.assertTrue(result['private_composed_arena_verified'])
        self.assertIs(type(result['angular_interval_algebra']['sealed_source_matches_current']),bool)
        self.assertFalse(result['angular_interval_algebra']['battle_connected'])
        self.assertFalse(result['public_gpu_admitted'])
        self.assertFalse(result['coordinate_skill_shape_contains_is_physical_landing'])
        self.assertFalse(result['logical_pellets_equal_emitted_packets'])
        numeric=result['deterministic_numeric_primitives']
        self.assertEqual(numeric['reference_kind'],'deterministic-common-cpu')
        self.assertEqual(numeric['contract'],'coordinate-binary64-v1')
        self.assertFalse(numeric['battle_connected'])
        self.assertFalse(numeric['full_numeric_policy_implemented'])
        geometry=result['deterministic_shape_geometry']
        self.assertTrue(geometry['authored_angles_consumed_on_gpu'])
        self.assertFalse(geometry['rotation_matrix_precomputed_on_cpu'])
        self.assertFalse(geometry['radial_integrator_connected'])
        self.assertFalse(geometry['battle_connected'])
        landing=result['deterministic_radial_landing']
        physical=result['coordinate_physical_expected']
        self.assertTrue(physical['runtime_connected'])
        self.assertEqual(physical['group_owner_mask_required'],0)
        self.assertFalse(physical['live_core_nodes_connected'])
        self.assertFalse(physical['rng_connected'])
        self.assertFalse(physical['public_gpu_admitted'])
        quantity=result['coordinate_packet_quantity']
        self.assertTrue(quantity['expanded_full_charge_parent_quantity_connected'])
        self.assertTrue(quantity['native_creation_and_landing_times_distinguished'])
        self.assertFalse(quantity['public_gpu_admitted'])
        accumulation=result['coordinate_target_accumulation']
        self.assertEqual(accumulation['classification'],'native_reference_exclusion')
        self.assertFalse(accumulation['extra_gpu_collection_required_for_parity'])
        self.assertTrue(accumulation['coordinate_accumulation_emission_connected'])
        emission=result['coordinate_accumulation_emission']
        self.assertTrue(emission['body_only_receipt_connected'])
        self.assertFalse(emission['public_gpu_admitted'])
        self.assertEqual(emission['excluded_coordinate_scenarios'],['ADD sharing','enemy attack nodes'])
        core=result['coordinate_live_core']
        self.assertTrue(core['runtime_connected'])
        self.assertTrue(core['graph_lifetime_reused'])
        self.assertTrue(core['default_auto_aim_tracks_selected_core'])
        self.assertFalse(core['public_gpu_admitted'])
        cache=result['coordinate_geometry_cache']
        self.assertTrue(cache['runtime_connected']);self.assertTrue(cache['shared_across_shooters'])
        self.assertEqual(cache['entries_127_targets'],231);self.assertFalse(cache['public_gpu_admitted'])
        matrix=result['coordinate_area_matrix']
        self.assertFalse(matrix['host_transcendentals_in_input'])
        self.assertTrue(matrix['shared_cache_executor'])
        self.assertTrue(matrix['historical_cpu_profile_retained'])
        self.assertFalse(matrix['public_gpu_admitted'])
        self.assertTrue(landing['prepared_frame_values_on_gpu'])
        self.assertTrue(landing['all_cuts_retained'])
        self.assertEqual(landing['cuts_capacity'],5098)
        self.assertFalse(landing['sampling_rng_connected'])
        self.assertFalse(landing['battle_connected'])
        self.assertEqual((result['gpu_calls'], result['native_battle_calls']), (0, 0))
        manual=result['coordinate_manual_actions']
        self.assertTrue(manual['common_runtime_connected']);self.assertTrue(manual['explicit_cover_hold_literals_packed'])
        self.assertFalse(manual['computed_cpu_action_schedule']);self.assertTrue(manual['charging_visibility_separate_from_phase'])
        self.assertFalse(manual['conditional_policies_connected']);self.assertFalse(manual['cover_all_connected'])
        self.assertFalse(manual['public_gpu_admitted']);self.assertFalse(manual['all_characters_certified'])
        self.assertIs(type(manual['sealed_source_matches_current']),bool)
        policies=result['coordinate_cover_policies']
        self.assertTrue(policies['common_runtime_connected']);self.assertTrue(policies['shared_anchor_and_prediction_clock'])
        self.assertEqual(len(policies['reload_policies']),4);self.assertTrue(policies['if_dry_connected'])
        self.assertFalse(policies['computed_cpu_action_schedule']);self.assertFalse(policies['cover_all_connected'])
        self.assertFalse(policies['public_gpu_admitted']);self.assertFalse(policies['all_characters_certified'])
        self.assertEqual((policies['input_words'],policies['output_words']),(109656,1769856))
        squad=result['coordinate_squad_actions']
        self.assertEqual(squad['authored_actions'],['focus','cover_all']);self.assertTrue(squad['live_owner_excluded'])
        self.assertFalse(squad['cover_all_requests_camera']);self.assertTrue(squad['stable_equal_time_order'])
        self.assertFalse(squad['computed_cpu_action_schedule']);self.assertFalse(squad['public_gpu_admitted'])
        self.assertEqual(squad['extra_runtime_bytes'],0);self.assertEqual(squad['output_padding_owned_words'],48)
        mode=result['coordinate_squad_mode_state']
        self.assertTrue(mode['character_mode_lifetime_connected']);self.assertTrue(mode['same_frame_reload_entry_wait'])
        self.assertEqual(mode['busy_state_shared_by'],['squad cover_all','pre-arbitration cover/reload policies'])
        self.assertEqual(mode['wire_version'],2);self.assertEqual(mode['extra_runtime_bytes'],0)
        self.assertFalse(mode['public_gpu_admitted']);self.assertFalse(mode['all_characters_certified'])
        burst=result['coordinate_burst_controls']
        self.assertTrue(burst['shared_candidate_selection_and_prediction']);self.assertTrue(burst['gpu_owned_stage_open_and_completed_cycles'])
        self.assertTrue(burst['tick_entry_stage_snapshot']);self.assertTrue(burst['cover_down_ordering_receipts'])
        self.assertFalse(burst['computed_cpu_action_schedule']);self.assertFalse(burst['public_gpu_admitted']);self.assertFalse(burst['all_characters_certified'])
        self.assertEqual((burst['input_words'],burst['output_words'],burst['extra_runtime_bytes']),(109968,1769856,0))
        actions=result['coordinate_mode_actions']
        self.assertTrue(actions['shared_manual_weapon_executor']);self.assertTrue(actions['base_charge_cover_cancels_post_delay'])
        self.assertTrue(actions['canonical_static_base_clock_checked']);self.assertFalse(actions['computed_cpu_action_schedule'])
        self.assertFalse(actions['public_gpu_admitted']);self.assertFalse(actions['all_characters_certified'])
        self.assertEqual((actions['input_words'],actions['output_words'],actions['extra_runtime_bytes']),(109968,1769856,0))
        auto=result['coordinate_automatic_reload']
        self.assertTrue(auto['shared_post_delay_phase']);self.assertTrue(auto['pending_survives_ineligible_shot'])
        self.assertTrue(auto['session_change_clears_pending']);self.assertTrue(auto['exact_notification_damage_and_final_latch_compared'])
        self.assertFalse(auto['computed_cpu_action_schedule']);self.assertFalse(auto['public_gpu_admitted']);self.assertFalse(auto['all_characters_certified'])
        original=result['coordinate_original']
        self.assertTrue(original['complete_original_roster_bridge']);self.assertTrue(original['shared_named_removal_handler'])
        self.assertTrue(original['omissions_must_match_native'])
        self.assertEqual(original['retained_history_capacity'],dict(team=1024,fractional=2048,projectile=2048))
        self.assertFalse(original['computed_cpu_action_schedule']);self.assertFalse(original['public_gpu_admitted']);self.assertFalse(original['all_characters_certified'])
        rows = {r['id']: r for r in result['dependencies']}
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows['physical-native-observation']['common_policy_reference_cli'],
                         'coordinate-physical-common')
        self.assertFalse(rows['physical-native-observation']['common_policy_is_historical_native_equivalence'])
        def visit(key, stack):
            self.assertNotIn(key, stack)
            for dep in rows[key]['depends_on']:visit(dep, stack | {key})
        for key in rows:visit(key, set())

    def test_new_interval_source_reports_stale_proof_without_blocking_development(self):
        name='gpu/coordinate_arc_sets.slang';text=(ROOT/name).read_text()
        report=verify(ROOT,{name:text+'\n// source changed, requires a new independent proof\n'})
        self.assertTrue(report['passed'])
        self.assertFalse(report['angular_interval_algebra']['sealed_source_matches_current'])
        self.assertTrue(report['angular_interval_algebra']['requires_new_metal_proof'])
        self.assertFalse(report['calculation_verified'])

    def test_changed_packet_probability_or_observation_requires_review(self):
        base = 'research/upstream/nikke-calc-master/calculator/'
        for name, old, new in [
                (base+'timeline.py', 'L.core_open / wb', 'L.core_under / wb'),
                (base+'timeline.py', 'round(r["damage"] * p)', 'r["damage"] * p'),
                (base+'timeline.py', 'angle=needs_angle(ax, ay, tg, geom.core)', 'angle=False'),
                (base+'aim.py', '_subtract(arcs, covered)', 'arcs'),
                ('research/world_projectile_native.py', 'len({h.damage for h in answer})==1', 'True'),
                ('app/battle_attack_group_runtime.py', 'ev.part_damage or ev.interrupt_damage', 'False')]:
            with self.subTest(name=name, old=old):
                text=(ROOT/name).read_text();self.assertIn(old,text)
                with self.assertRaises(AssertionError):verify(ROOT,{name:text.replace(old,new,1)})

    def test_common_policy_cannot_silently_revert_to_host_landing(self):
        name='research/world_coordinate_physical_common.py';text=(ROOT/name).read_text()
        with self.assertRaises(AssertionError):
            verify(ROOT,{name:text.replace("patch.object(boss_pattern, 'landing', common_landing)",
                                           "patch.object(boss_pattern, 'landing', boss_pattern.landing)")})

    def test_cli_writes_once_without_backend_or_native_execution(self):
        path=ROOT/'scripts/nikke_gpu.py';spec=importlib.util.spec_from_file_location('frontier_cli',path)
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'report.json'
            with contextlib.redirect_stdout(io.StringIO()),patch.object(cli,'native_hash',side_effect=AssertionError('No native execution')):
                cli.main(['model-check','--out',str(out)])
            self.assertTrue(out.is_file())
            with self.assertRaises(ValueError):cli.main(['model-check','--out',str(out)])


if __name__=='__main__':unittest.main()
