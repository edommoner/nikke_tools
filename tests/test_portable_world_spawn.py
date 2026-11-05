"""Full-native startup/add notification and ordering contracts."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
s=importlib.util.spec_from_file_location('spawn_test_suite',ROOT/'research/verify-world-spawn.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
class SpawnContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={c['name']:c for c in suite.fixtures()};cls.observed={n:suite.inspect_native(c) for n,c in cls.rows.items()}
 def native(self,n):return self.observed[n][0]
 def test_initial_team_notice_is_once_per_owner(self):self.assertEqual(self.native('spawn-once-idle')['enemy_spawn_notifications'],[dict(owner=i,time=0.0) for i in range(5)])
 def test_add_notifications_are_per_actor_and_in_owner_order(self):
  notes=self.native('startup-plus127-adds')['enemy_spawn_notifications'];self.assertEqual(len(notes),640);self.assertEqual([n['owner'] for n in notes],list(range(5))*128)
 def test_delayed_spawns_follow_the_accumulated_native_frame_clock(self):
  t=0.0
  for _ in range(12):t+=1/60
  self.assertEqual(self.native('startup-plus-two-delayed-adds')['enemy_spawn_notifications'][5:],[dict(owner=i,time=t) for i in range(5)]*2)
 def test_all_battle_start_owners_complete_before_spawn(self):self.assertEqual(self.native('all-battle-start-owners-before-spawn')['named_state']['allied_carriers'][-1]['name'],'spawn')
 def test_startup_buff_changes_the_initial_magazine(self):self.assertEqual(self.native('spawn-before-magazine-initialization')['ammo'][0],1045)
 def test_trigger_budget_is_shared_between_startup_and_add_notices(self):
  for n in (1,2):self.assertEqual(self.native('spawn-global-trigger-limit-'+str(n))['named_state']['allied_carriers'][0]['stack'],n)
 def test_startup_dot_uses_the_existing_initial_timer_pass(self):
  trace=self.observed['spawn-dot_damage'][1];self.assertEqual((trace[0]['created'],trace[0]['landed']),(0.0,0.0))
 def test_all128_damage_receivers_use_literal_wide_selection(self):
  for family in ('bonus_damage','dot_damage'):
   name='spawn-'+family+'-all128-once';trace=self.observed[name][1];self.assertEqual(len(trace[0]['recipients']),128)
   w,_,_=suite.compile_case(self.rows[name]);self.assertEqual(w[suite.L['DAMAGE_DEFINITION_BASE']+1],128)
 def test_compiled_notification_uses_original_event_identity_and_candidate_mask(self):
  w,_,_=suite.compile_case(self.rows['spawn-once-idle']);self.assertEqual(w[suite.L['EVENT_BASE']],5);self.assertEqual(w[suite.L['EVENT_CANDIDATE_BASE']+5*suite.L['MASK_WORDS']],1)
 def test_gpu_input_excludes_observed_notification_results(self):
  c=copy.deepcopy(self.rows['spawn-once-idle']);w=suite.compile_case(c)[0];c['enemy_spawn_notifications']=[dict(owner=0,time=999)];self.assertEqual(w,suite.compile_case(c)[0]);self.assertEqual(w[0],suite.L['WORLD_SPAWN_ABI']);self.assertEqual(w[suite.L['TARGET_COUNTER_INPUT_BASE']+6],15)
 def test_trace_capacity_does_not_overlap_enemy_attack_or_periodic_banks(self):
  L=suite.L;self.assertEqual(L['WORLD_SPAWN_HEAD_BASE'],L['WORLD_ENEMY_ATTACK_BASE']+128*2);self.assertEqual(L['WORLD_SPAWN_TRACE_BASE'],L['WORLD_SPAWN_HEAD_BASE']+8);self.assertLessEqual(L['WORLD_SPAWN_TRACE_BASE']+4096*4,L['WORLD_PERIODIC_OUTPUT_WORDS'])
if __name__=='__main__':unittest.main()
