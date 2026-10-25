"""Routing requires source evidence; source drift cannot become noop admission."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_model_gap_audit import verify,MISSING_STATS
class GapAuditTests(unittest.TestCase):
 def test_current_sources_distinguish_missing_models_from_missing_ports(self):
  r=verify(ROOT);self.assertEqual(set(r['missing_stats']),set(MISSING_STATS));self.assertFalse(r['gpu_supported']);self.assertTrue(r['enemy_ammo']['named_completion_outside_target_loop']);self.assertFalse(r['target_and_nearby']['nearby_spatial_world'])
 def test_coordinate_geometry_is_a_port_gap_with_an_existing_native_consumer(self):
  r=verify(ROOT)['coordinate_world'];self.assertEqual(r['classification'],'gpu_port_gap');self.assertTrue(r['native_model_available']);self.assertFalse(r['gpu_connected'])
  self.assertTrue({'acos','atan2','cos','hypot','radians','sin'} <= set(r['native_math_calls']));self.assertTrue(r['native_pow_operator'])
  path='research/upstream/nikke-calc-master/calculator/timeline.py';text=(ROOT/path).read_text()
  for old,new in [('hit = [g for g in geom.targets if g.kind == "parts"]', 'hit = [g for g in geom.targets if g.kind == "interrupt"]'), ('g.shape.contains(ax, ay, grow)', 'True')]:
   changed=text.replace(old,new);self.assertNotEqual(text,changed)
   with self.assertRaises(AssertionError):verify(ROOT,{path:changed})
 def test_coordinate_host_math_policy_gap_is_source_bound_and_not_admitted(self):
  r=verify(ROOT)['coordinate_world'];n=r['numeric_frontend'];self.assertEqual(n['classification'],'gpu_numeric_implementation_gap');self.assertTrue(n['host_math_affects_selection']);self.assertTrue(n['common_policy_selected']);self.assertEqual(n['selected_policy'],'deterministic-shared-numeric');self.assertFalse(n['policy_implemented']);self.assertFalse(r['gpu_connected'])
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
