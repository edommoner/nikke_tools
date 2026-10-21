"""Ownership, shared counters and authored-only team compiler contracts."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
s=importlib.util.spec_from_file_location('team_test_suite',ROOT/'research/verify-world-team.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
class TeamContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows={c['name']:c for c in suite.fixtures()};cls.native={n:suite.inspect_native(c)[0] for n,c in cls.rows.items()}
 def test_static_lowering_binds_actual_attacker_and_preserves_condition_owner(self):
  w,m,_=suite.compile_case(self.rows['part-owner4-target-self']);self.assertEqual(m['binding_owners'],list(range(5)));self.assertEqual(m['team_condition_owners'],[5]*5);self.assertEqual(m['team_budget_keys'],[1]*5);self.assertEqual(m['binding_source_indices'],[0]*5)
 def test_self_recipients_are_each_actual_attacker(self):
  cs=self.native['part-owner4-target-self']['named_state']['allied_carriers'];self.assertEqual({c['owner'] for c in cs},set(range(5)));self.assertTrue(all(c['recipients']==[c['owner']] for c in cs))
 def test_all_allies_receives_each_attackers_carrier(self):self.assertTrue(all(c['recipients']==list(range(5)) for c in self.native['part-owner4-target-all_allies']['named_state']['allied_carriers']))
 def test_condition_uses_source_owner(self):self.assertTrue(all(c['stack']==1 for c in self.native['part-owner4-condition-attacker-is-not-condition-owner']['named_state']['allied_carriers']))
 def test_counter_crosses_attackers_and_pellets(self):
  n=self.native['part-three-pellets-team-counter'];self.assertEqual(sum(c['stack'] for c in n['named_state']['allied_carriers']),n['team_counts'][0]//3)
 def test_max_trigger_is_one_budget_across_all_attackers(self):
  for b in (1,3,7):self.assertEqual(sum(c['stack'] for c in self.native['team-shared-budget-'+str(b)]['named_state']['allied_carriers']),b)
 def test_probability_is_one_accumulator_across_attackers(self):
  for p in (25,50,100):
   n=self.native['team-shared-probability-'+str(p)];self.assertEqual(sum(c['stack'] for c in n['named_state']['allied_carriers']),int(n['team_counts'][0]*p/100))
 def test_source_down_stops_listener_without_stopping_team_count(self):
  n=self.native['team-source-down-counts-continue'];self.assertTrue(n['allies'][4]['down']);self.assertGreater(n['team_counts'][0],sum(c['stack'] for c in n['named_state']['allied_carriers']))
 def test_body_and_part_counts_are_distinct(self):
  n=self.native['team-body-rejects-parts-listener'];self.assertEqual(n['team_counts'][0],0);self.assertGreater(n['team_counts'][1],0);self.assertFalse(n['named_state']['allied_carriers'])
 def test_no_selected_recipient_leaves_no_carrier(self):self.assertFalse(self.native['team-no-recipient-keeps-budget']['named_state']['allied_carriers'])
 def test_native_core_fraction_is_binary64_noncore_credit(self):
  n=self.native['team-core-fraction-10'];cores={(r['owner'],r['time']):r['fraction'] for r in n['fractional_hits'] if r['event']==23}
  self.assertTrue(all(r['fraction']==1-cores[r['owner'],r['time']] for r in n['team_hits']))
 def test_full_core_rate_does_not_create_team_accumulator(self):self.assertFalse(self.native['team-core-fraction-100']['team_accumulators'])
 def test_compilation_cannot_run_a_native_or_gpu_battle(self):
  import portable_backend
  from calculator import timeline
  with patch.object(timeline,'simulate',side_effect=AssertionError('Native battle forbidden')),patch.object(portable_backend,'build',side_effect=AssertionError('GPU forbidden')),patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
   c=copy.deepcopy(self.rows['part-owner4-target-self']);a=suite.compile_case(c)[0];c['team_counts']=[9999,9999];c['team_hits']=[1];self.assertEqual(a,suite.compile_case(c)[0])
 def test_mixed_periodic_and_mode_team_listeners_fail_closed(self):
  for change in (dict(trigger=dict(timing=['part_hit_count:1','battle_start'],condition=[])),dict(tick_interval=.1),dict(type='weapon_change')):
   c=copy.deepcopy(self.rows['part-owner4-target-self']);c['effects'][0].update(change)
   with self.assertRaises(Exception):suite.compile_case(c)
 def test_unlowered_public_event_validation_rejects_team(self):
  from portable_trigger_specs import pack_descriptors
  row=[0]*201;row[144]=1;row[145:152]=[44,1,1,-1,0,0,-1]
  with self.assertRaises(ValueError):pack_descriptors([],0,row,suite.L,{},lambda v:[0,0],world_frame=False)
 def test_duplicate_timing_index_matches_native_multiplicity(self):
  n=self.native['team-duplicate-event-timings-native-index-multiplicity'];self.assertEqual(sum(c['stack'] for c in n['named_state']['allied_carriers']),2*n['team_counts'][0])
 def test_source_owner_target_predicate_handles_add_death(self):
  present=self.native['team-source-owner-target_state:team-mark']['named_state']['allied_carriers'];absent=self.native['team-source-owner-not_target_state:team-mark']['named_state']['allied_carriers']
  self.assertTrue(present);self.assertFalse(absent);self.assertEqual(sum(c['stack'] for c in present),18)
 def test_team_banks_follow_fraction_banks(self):
  L=suite.L;self.assertEqual(L['WORLD_TEAM_STATE_BASE'],L['WORLD_FRACTION_TRACE_BASE']+L['WORLD_FRACTION_TRACE_COUNT']*8);self.assertLessEqual(L['WORLD_TEAM_TRACE_BASE']+L['WORLD_TEAM_TRACE_COUNT']*8,L['WORLD_PERIODIC_OUTPUT_WORDS'])
if __name__=='__main__':unittest.main()
