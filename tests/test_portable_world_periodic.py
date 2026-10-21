"""Native ownership and timing contracts for the shared wide periodic path."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
import world_periodic_cases as cases
class PeriodicContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={c['name']:c for c in cases.fixtures()}
 def inspect(self,name):return cases.suite.inspect_native(self.rows[name])
 def test_alias_keeps_the_existing_packet_and_unions_future_ticks(self):
  n,t=self.inspect('periodic-alias-union-freezes-existing-tick');self.assertEqual([r['row'] for r in t],[0]*6)
  self.assertEqual([r['recipients'] for r in t[:2]],[[0,1],[0,1]]);self.assertEqual(t[2]['recipients'],[0,1,2]);self.assertEqual(len(n['periodic_runtime']['timers']),1)
 def test_captured_dot_does_not_bind_the_reopened_actor_generation(self):
  n,t=self.inspect('periodic-target-state-reopened-generation');self.assertTrue(all(r['recipients']==[0] for r in t))
  self.assertEqual([r['present'] for r in n['named_state']['queries']],[True,False])
 def test_counter_immediate_tick_samples_after_the_counter_buff(self):
  _,t=self.inspect('dot-immediate-samples-after-counter-buff');self.assertEqual(t[0]['created'],1/60);self.assertEqual(t[0]['landed'],1/60);self.assertGreater(t[0]['amount'],242)
 def test_captured_membership_excludes_a_late_wave_from_named_predicates(self):
  n,_=self.inspect('periodic-target-state-body-initial-and-late');self.assertEqual([r['present'] for r in n['named_state']['queries']],[True,True,False])
 def test_generic_periodic_damage_keeps_all_three_hits(self):
  _,t=self.inspect('non-dot-periodic-sequential_damage:3');self.assertEqual(len(t),9);self.assertEqual([r['hit'] for r in t],[1,2,3]*3)
 def test_runtime_target_condition_observes_the_dot_carrier(self):
  _,t=self.inspect('periodic-live-runtime-target-state');self.assertTrue(all(r['amount']==376 for r in t))
 def test_counter_ordinal_includes_the_native_periodic_carrier(self):
  n,_=self.inspect('periodic-dot-counter-before-child-damage');self.assertEqual(n['target_counters']['completions'][0]['entry_ordinal'],2)
 def test_gpu_input_uses_only_authored_programs(self):
  c=copy.deepcopy(self.rows['periodic-all128']);before=cases.compile_case(c)[0];c['native']={'targets':[0]*128,'damage':1e30};self.assertEqual(before,cases.compile_case(c)[0])
 def test_snapshots_cover_all_definitions_and_landing_slots_without_overlap(self):
  L=cases.L;self.assertGreaterEqual(L['WORLD_PERIODIC_DEFINITION_BASE'],524288)
  self.assertEqual(L['WORLD_PERIODIC_PACKET_BASE']-L['WORLD_PERIODIC_DEFINITION_BASE'],256*38)
  self.assertEqual(L['WORLD_PERIODIC_HEAD_BASE']-L['WORLD_PERIODIC_PACKET_BASE'],L['LANDINGS']*38)
  self.assertLessEqual(L['WORLD_PERIODIC_HEAD_BASE']+16,L['WORLD_PERIODIC_OUTPUT_WORDS'])
if __name__=='__main__':unittest.main()
