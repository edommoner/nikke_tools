"""Routing requires source evidence; source drift cannot become noop admission."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_model_gap_audit import verify,MISSING_STATS
class GapAuditTests(unittest.TestCase):
 def test_current_sources_distinguish_missing_models_from_missing_ports(self):
  r=verify(ROOT);self.assertEqual(set(r['missing_stats']),set(MISSING_STATS));self.assertFalse(r['gpu_supported']);self.assertTrue(r['enemy_ammo']['named_completion_outside_target_loop']);self.assertFalse(r['target_and_nearby']['nearby_spatial_world'])
 def test_private_membership_proof_keeps_spatial_and_full_profile_open(self):
  lock=verify(ROOT)['missing_stats']['lock_on'];r=lock['declared_shared_membership_executor']
  self.assertTrue(r['actual_world_actor_pools']);self.assertTrue(r['named_capacity_reader_connected'])
  self.assertEqual(r['actor_capacity'],128);self.assertFalse(r['spatial_selection_verified'])
  self.assertFalse(r['public_admission']);self.assertFalse(r['original_full_profile_verified'])
  self.assertFalse(lock['unlocked_candidate_exclusion_verified'])
 def test_enemy_lock_carrier_proof_does_not_certify_distance_or_full_profile(self):
  r=verify(ROOT);p=r['missing_stats']['lock_on']['declared_enemy_carrier_executor']
  self.assertEqual(p['original_indices_preserved'],[0,1,2,6,20]);self.assertTrue(p['actual_enemy_carriers']);self.assertTrue(p['metal_verified'])
  for key in ('cuda_verified','spatial_selection_verified','full_profile_verified','game_verified','public_admission'):self.assertFalse(p[key])
  self.assertFalse(r['full_goal_complete'])
 def test_complete_original_roster_probe_retains_remaining_model_and_branch_gaps(self):
  r=verify(ROOT);p=r['missing_stats']['lock_on']['complete_original_roster_composition']
  self.assertEqual(p['original_source_definitions'],25);self.assertEqual(p['complete_roster_definitions'],91)
  self.assertEqual(p['durations_seconds'],[3,30]);self.assertEqual(p['preclaim_native_history_budgets'],13)
  self.assertEqual(p['unobserved_native_activation_indices'],[2]);self.assertEqual(len(p['observed_native_activation_indices']),24)
  self.assertTrue(p['actual_enemy_marker_sequential_and_projectile_executors_composed']);self.assertTrue(p['metal_verified'])
  for key in ('cuda_verified','spatial_selection_verified','all_conditional_branches_verified','game_verified','public_admission','full_profile_verified','full_character_certified'):self.assertFalse(p[key])
  self.assertFalse(r['full_goal_complete'])
 def test_original_control_probe_preserves_remaining_spatial_and_character_gaps(self):
  r=verify(ROOT);p=r['missing_stats']['lock_on']['original_control_and_saturation_composition']
  self.assertEqual((p['native_cases'],p['rejected_cases']),(9,8));self.assertEqual(p['cover_source_row'],2)
  self.assertEqual(p['native_activation_entry_coverage_across_suites'],25);self.assertTrue(p['native_entry_coverage_is_not_all_branch_certification'])
  self.assertEqual(p['burst_distinct_targets'],15);self.assertEqual(p['burst_uses_before_base_restored'],2)
  self.assertTrue(p['metal_verified']);self.assertTrue(p['independently_sealed']);self.assertTrue(p['burst_target_saturation_verified'])
  for key in ('cuda_verified','spatial_selection_verified','death_retarget_verified','parts_and_injury_branches_verified','all_conditional_branches_verified','game_verified','public_admission','full_character_certified'):self.assertFalse(p[key])
  self.assertFalse(r['full_goal_complete'])
 def test_lock_capacity_is_not_the_observed_canonical_marker_stack(self):
  r=verify(ROOT);lock=r['missing_stats']['lock_on'];public=lock['published_skill_contract']
  self.assertTrue(lock['marker_stack_count_is_not_distinct_target_count']);self.assertFalse(lock['unlocked_candidate_exclusion_verified'])
  self.assertTrue(public['selection']['exclude_existing_locks']);self.assertEqual(public['target_capacity'],dict(ordinary_distinct_targets=5,burst_additional_targets=10))
  self.assertFalse(public['in_game_validation_performed']);self.assertEqual(len(public['unresolved_rules']),5)
  target=r['missing_stats']['effect_target_count_add']['required_consumer_contract']
  self.assertTrue(target['distinct_target_capacity']);self.assertTrue(target['does_not_increase_per_target_marker_stack']);self.assertEqual(target['duration_bullets'],2);self.assertFalse(target['implementation_verified'])
  self.assertFalse(r['gpu_supported']);self.assertFalse(r['full_goal_complete'])
  path=public['fixture'];original=json.loads((ROOT/path).read_text())
  for key,value in [('exclude_existing_locks',False),('interval_seconds',0.1)]:
   changed=json.loads(json.dumps(original));changed['selection'][key]=value
   with self.subTest(key=key),self.assertRaises(AssertionError):verify(ROOT,{path:json.dumps(changed)})
  original['in_game_validation_performed']=True
  with self.assertRaises(AssertionError):verify(ROOT,{path:json.dumps(original)})
 def test_coordinate_geometry_is_a_port_gap_with_an_existing_native_consumer(self):
  r=verify(ROOT)['coordinate_world'];self.assertEqual(r['classification'],'gpu_port_gap');self.assertTrue(r['native_model_available']);self.assertFalse(r['gpu_connected'])
  self.assertTrue({'acos','atan2','cos','hypot','radians','sin'} <= set(r['native_math_calls']));self.assertTrue(r['native_pow_operator'])
  path='research/upstream/nikke-calc-master/calculator/timeline.py';text=(ROOT/path).read_text()
  for old,new in [('hit = [g for g in geom.targets if g.kind == "parts"]', 'hit = [g for g in geom.targets if g.kind == "interrupt"]'), ('g.shape.contains(ax, ay, grow)', 'True')]:
   changed=text.replace(old,new);self.assertNotEqual(text,changed)
   with self.assertRaises(AssertionError):verify(ROOT,{path:changed})
 def test_coordinate_host_math_policy_gap_is_source_bound_and_not_admitted(self):
  r=verify(ROOT)['coordinate_world'];n=r['numeric_frontend'];self.assertEqual(n['classification'],'gpu_numeric_implementation_gap');self.assertTrue(n['host_math_affects_selection']);self.assertTrue(n['common_policy_selected']);self.assertEqual(n['selected_policy'],'deterministic-shared-numeric');self.assertFalse(n['policy_implemented']);self.assertFalse(r['gpu_connected'])
  self.assertIn('public coordinate frontend',n['policy_implemented_scope']);self.assertTrue(n['public_admission_remaining']);self.assertIn('coordinate-landing-arena',n['private_suites']);self.assertIn('Evidence locations only',n['private_suite_list_scope'])
  self.assertEqual(n['resident_integration_suite'],'coordinate-resident-frames');self.assertTrue(n['resident_frame_independently_audited']);self.assertFalse(n['resident_frame_cuda_device_verified']);self.assertFalse(n['resident_frame_public_admission_verified'])
  path='research/upstream/nikke-calc-master/calculator/aim.py';text=(ROOT/path).read_text();changed=text.replace('math.cos(th)','1.0');self.assertNotEqual(text,changed)
  with self.assertRaisesRegex(AssertionError,'numeric source drift'):verify(ROOT,{path:changed})
 def test_coordinate_guard_change_requires_port_evidence(self):
  path='app/portable_world_roster_input.py';text=(ROOT/path).read_text()
  changed=text.replace("(enemy.get('coord') is not None and not coordinate) or ", '');self.assertNotEqual(text,changed)
  with self.assertRaisesRegex(AssertionError,'Coordinate GPU admission changed'):verify(ROOT,{path:changed})
  changed=text.replace('coordinate=False','coordinate=True');self.assertNotEqual(text,changed)
  with self.assertRaisesRegex(AssertionError,'Coordinate GPU admission changed'):verify(ROOT,{path:changed})
 def test_private_bridge_does_not_certify_public_coordinate_admission(self):
  r=verify(ROOT)['coordinate_world'];self.assertTrue(r['private_roster_opt_in_available']);self.assertTrue(r['public_enemy_coordinate_rejection_verified']);self.assertFalse(r['gpu_connected'])
  path='app/engine_worker.py';text=(ROOT/path).read_text();changed=text.replace("allowed_enemy = {'def',", "allowed_enemy = {'coord', 'def',");self.assertNotEqual(text,changed)
  with self.assertRaisesRegex(AssertionError,'Public coordinate admission changed'):verify(ROOT,{path:changed})
 def test_new_consumer_or_changed_spec_forces_review(self):
  base='research/upstream/nikke-calc-master/'
  path=base+'calculator/timeline.py';original=(ROOT/path).read_text()
  with self.assertRaises(AssertionError):verify(ROOT,{path:original+'\ndef future_consumer():\n    return "lock_on"\n'})
  path=base+'docs/IMPL-STATUS.md';original=(ROOT/path).read_text();line=next(x for x in original.splitlines() if x.startswith('| `lock_on` |'))
  with self.assertRaises(AssertionError):verify(ROOT,{path:original.replace(line,line.replace('❌','✅'))})
 def test_enemy_ammo_filter_and_nearby_branch_cannot_silently_change(self):
  base='research/upstream/nikke-calc-master/'
  path=base+'calculator/timeline.py';original=(ROOT/path).read_text();self.assertIn('allies = [n for n in names if n in char_states]',original)
  with self.assertRaises(AssertionError):verify(ROOT,{path:original.replace('allies = [n for n in names if n in char_states]','allies = list(names)')})
  path=base+'calculator/boss_pattern.py';original=(ROOT/path).read_text()
  # New real target policy must invalidate the previous missing-branch evidence.
  start=original.index('    def _ranked(');changed=original[:start]+original[start:].replace('        alive = self._alive_adds()','        nearby = "target_and_nearby"\n        alive = self._alive_adds()',1)
  self.assertNotEqual(original,changed)
  with self.assertRaises(AssertionError):verify(ROOT,{path:changed})
 def test_all_remaining_source_gap_routes_remain_closed(self):
  from portable_readiness_semantics import reference_readiness
  for stat in MISSING_STATS:
   r=reference_readiness(dict(phase='effect',category='effect',kind='buff',stat=stat,target='self',scaling=None));self.assertEqual(r['lane'],'reference_model_gap');self.assertFalse(r['gpu_supported'])
if __name__=='__main__':unittest.main()
