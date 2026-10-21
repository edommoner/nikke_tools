"""Native hold/priority/camera contracts and static-only input normalization."""
import copy,importlib.util,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
import engine_worker
from calculator import timeline
from portable_charge_control_specs import normalize_static_controls,compile_policy,parse_hold,THRESHOLD_BASE,WORDS
from world_charge_control_cases import fixtures
from world_charge_control_native import observe
from world_frame_native import roster_names,authored_metadata
class ChargeControls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows={c['name']:c for c in fixtures()};cls.native={n:observe(c)[0] for n,c in cls.rows.items() if not n.endswith('simultaneous-strict')}
 def row(self,name):return self.rows['manual-charge-'+name]
 def native_case(self,name):return self.native['manual-charge-'+name]
 def normalize(self,case,changes=None):
  names=roster_names(case);chars=[dict(name=n,control=copy.deepcopy(ctrl),skill_levels={'1':10,'2':10,'3':10}) for n,ctrl in zip(names,case['controls'])]
  if changes:changes(chars)
  with patch.dict(timeline._NIKKE,authored_metadata(case)),patch.dict(timeline._DELAYS['_exceptions'],{},clear=True),patch.dict(timeline._DELAYS['_defaults_by_weapon_type'],{'AR':{'post_reload_delay':0}},clear=True):return normalize_static_controls(chars,case['base_atk'],case['enemy'],case['control_mode'])
 def pack(self,case):
  names=roster_names(case);states={}
  for e in case['effects']:
   for timing in e['trigger']['timing']:
    parsed=parse_hold(timing)
    if parsed:states.setdefault('charge_hold:'+parsed[0],len(states))
  return compile_policy(self.normalize(case),list(zip(case['effects'],case['owners'])),names,states,0),states
 def test_static_normalizer_cannot_tick_or_execute_a_battle(self):
  import portable_backend
  with patch.object(timeline,'simulate',side_effect=AssertionError('CPU battle forbidden')),patch.object(timeline.CharState,'tick',side_effect=AssertionError('CPU tick forbidden')),patch.object(portable_backend,'build',side_effect=AssertionError('GPU forbidden')),patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):self.pack(self.row('sequence-until-0.8'))
 def test_raw_threshold_aliases_remain_distinct_and_native_sorted(self):
  w,states=self.pack(self.row('raw-alias-order'));actual=[(w[THRESHOLD_BASE+i*4+1],struct.unpack('<d',struct.pack('<II',*w[THRESHOLD_BASE+i*4+2:THRESHOLD_BASE+i*4+4]))[0]) for i in range(w[4])]
  self.assertEqual(actual,[(states['charge_hold:'+s],float(s)) for s in ('0','0.1','0.10','0.2')])
 def test_aliases_notify_at_the_same_frame_in_raw_lexical_order(self):
  notes=self.native_case('raw-alias-order')['manual_control']['notifications'];self.assertEqual([r['event'] for r in notes[:4]],['charge_hold:0','charge_hold:0.1','charge_hold:0.10','charge_hold:0.2']);self.assertEqual(notes[1]['time'],notes[2]['time'])
 def test_positive_hold_threshold_does_not_fire_without_manual_holding(self):self.assertEqual(self.native_case('automatic-0.1')['manual_control']['notifications'],[])
 def test_zero_threshold_is_one_notification_per_completed_charge(self):
  n=self.native_case('automatic-0');self.assertEqual(len(n['manual_control']['notifications']),n['shots'][0]);self.assertTrue(all(r['time']==r['full_time'] for r in n['manual_control']['notifications']))
 def test_releasing_before_threshold_does_not_emit_it(self):self.assertEqual(self.native_case('sequence-until-0.3')['manual_control']['notifications'],[])
 def test_full_charge_stays_latched_after_speed_buff_expires(self):
  r=self.native_case('completed-charge-survives-speed-expiry')['manual_control']['notifications'][0];self.assertLess(r['full_time'],.15);self.assertGreater(r['time'],.15);self.assertGreaterEqual(r['time']-r['full_time'],.2)
 def test_down_cancels_an_active_hold(self):
  n=self.native_case('owner-down-while-holding');self.assertTrue(n['allies'][0]['down']);c=n['manual_control']['characters'][0];self.assertEqual((c['phase'],c['full_time'],c['release_time']),('ready',-1.,-1.));self.assertEqual(n['manual_control']['arbitration'][-1]['owner'],-1)
 def test_new_mode_callback_preserves_the_old_charge_until_physical_entry(self):
  c=self.native_case('critical-child-new-mode-snapshot')['manual_control']['characters'][0];self.assertEqual(c['phase'],'charging');self.assertGreater(c['full_time'],0);self.assertEqual(c['release_time'],.8)
 def test_dynamic_window_hold_has_a_typed_open_end_without_nan_json(self):
  c=self.native_case('state-window-open-snapshot')['manual_control']['characters'][0];self.assertIsNone(c['release_time']);self.assertTrue(c['release_until_close']);self.assertEqual(c['phase'],'charging');self.assertEqual(c['full_time'],-1.)
 def test_policy_reentry_is_allowed_once_for_the_same_burst_anchor(self):
  n=self.native_case('policy-reentry-only-once')['manual_control'];self.assertEqual(n['preemptions'][0],2);self.assertEqual(len(n['characters'][0]['reentry_anchors']),1);self.assertEqual(len([r for r in n['notifications'] if r['owner']==0]),2)
 def test_control_input_and_output_banks_do_not_overlap_previous_layouts(self):
  from portable_specs import LIMITS as L
  self.assertEqual(L['WORLD_CONTROL_INPUT_WORDS'],L['WORLD_TEAM_INPUT_WORDS']+WORDS);self.assertEqual(L['WORLD_CONTROL_STATE_BASE'],L['WORLD_TEAM_TRACE_BASE']+L['WORLD_TEAM_TRACE_COUNT']*8);self.assertEqual(L['WORLD_CONTROL_HISTORY_BASE']+5*16*2,L['WORLD_CONTROL_TRACE_BASE']);self.assertLessEqual(L['WORLD_CONTROL_TRACE_BASE']+L['WORLD_CONTROL_TRACE_COUNT']*8,L['WORLD_PERIODIC_OUTPUT_WORDS'])
 def test_down_charge_automatic_uses_its_own_static_input_kind(self):
  w,_=self.pack(self.row('down-charge-automatic'));self.assertEqual(w[16+4],2);n=self.native_case('down-charge-automatic');self.assertEqual(len(n['manual_control']['notifications']),n['shots'][0])
 def test_hold_sequence_on_auto_weapon_is_consumed_without_holding(self):
  n=self.native_case('auto-weapon-ignores-hold')['manual_control'];self.assertFalse(n['notifications']);self.assertEqual(n['characters'][0]['sequence_index'],1);self.assertEqual(n['characters'][0]['phase'],'ready');self.assertEqual([r['owner'] for r in n['arbitration']],[0,-1])
 def test_ammo_removal_preserves_charge_for_later_alias_condition(self):
  n=self.native_case('ammo-removal-retains-charge-for-second-alias');notes=n['manual_control']['notifications'];self.assertEqual([r['event'] for r in notes[:2]],['charge_hold:0.1','charge_hold:0.10']);self.assertEqual(notes[1]['full_time'],notes[0]['full_time']);self.assertGreater(notes[1]['full_time'],0);self.assertTrue(any(c['name']=='still-charging' for c in n['named_state']['allied_carriers']))
 def test_count_requires_repeated_charges(self):
  n=self.native_case('repeated-charge-count');self.assertGreaterEqual(len(n['manual_control']['notifications']),2);self.assertEqual(sum(c['stack'] for c in n['named_state']['allied_carriers']),len(n['manual_control']['notifications'])//2)
 def test_equal_priority_new_edge_preempts_and_changes_camera(self):
  rows=self.native_case('same-priority-new-request-preempts')['manual_control']['arbitration'];self.assertEqual([r['owner'] for r in rows],[0,1,-1]);self.assertEqual(rows[1]['camera_mask'],2);self.assertEqual(rows[1]['preemptions'],[1,0,0,0,0])
 def test_simultaneous_requests_use_squad_order_in_solo(self):self.assertEqual(self.native_case('simultaneous-solo')['manual_control']['arbitration'][0]['owner'],0)
 def test_warn_uses_static_camera_while_allowing_both_holds(self):
  n=self.native_case('simultaneous-warn')['manual_control'];self.assertEqual({r['owner'] for r in n['notifications']},{0,1});self.assertTrue(all(r['camera_mask']==0 and r['owner']==-1 for r in n['arbitration']))
 def test_strict_rejects_real_runtime_overlap(self):
  with self.assertRaisesRegex(ValueError,'같은 시각'):observe(self.row('simultaneous-strict'))
 def test_threshold_is_consumed_even_if_full_burst_condition_fails(self):
  a=self.native_case('own_full_burst-not_during_full_burst');b=self.native_case('own_full_burst-during_full_burst');self.assertEqual(a['manual_control']['notifications'],b['manual_control']['notifications']);self.assertEqual(len(a['manual_control']['notifications']),1);self.assertFalse(a['named_state']['allied_carriers']);self.assertTrue(b['named_state']['allied_carriers'])
 def test_judge_policy_moves_notification_after_full_burst(self):
  a=self.native_case('charge_hold_after_fb-not_during_full_burst');b=self.native_case('charge_hold_after_fb-during_full_burst');self.assertEqual(a['manual_control']['notifications'],b['manual_control']['notifications']);self.assertGreater(a['manual_control']['notifications'][0]['time'],10);self.assertTrue(a['named_state']['allied_carriers']);self.assertFalse(b['named_state']['allied_carriers'])
 def test_input_is_independent_of_observed_notifications_and_owners(self):
  c=copy.deepcopy(self.row('sequence-until-0.8'));a=self.pack(c)[0];c['observed_notifications']=[dict(time=0,owner=4)];c['observed_camera']=31;self.assertEqual(a,self.pack(c)[0]);self.assertEqual(len(a),WORDS)
 def test_down_charge_rejects_literal_hold_during_construction(self):
  c=copy.deepcopy(self.row('sequence-until-0.8'));c['weapon_metadata']['input_type']='DOWN_Charge'
  with self.assertRaisesRegex(ValueError,'DOWN_Charge'):self.normalize(c)
 def test_nonfinite_negative_and_malformed_thresholds_reject(self):
  for t in ('charge_hold:nan','charge_hold:inf','charge_hold:-1','charge_hold_count:0.1:0','charge_hold_count:0.1:1.5','charge_hold_count:0.1:2147483648'):
   with self.subTest(t=t),self.assertRaises(ValueError):parse_hold(t)
 def test_opaque_finite_raw_spellings_are_preserved(self):self.assertEqual(parse_hold('charge_hold:1e-1'),('1e-1',.1,1))
 def test_pending_adapter_families_fail_closed(self):
  for control in (dict(click=[dict(mode='tap',window='always',rate=2)]),dict(click=[dict(mode='hold',anchor='combat_start',offset=0,len=1)]),dict(sequence=[dict(action='cover',t=0,duration=1)])):
   c=copy.deepcopy(self.row('sequence-until-0.8'));c['controls'][0]=control
   with self.assertRaises(ValueError):self.normalize(c)
 def test_capacity_is_not_silently_truncated(self):
  c=copy.deepcopy(self.row('sequence-until-0.8'));c['controls'][0]['sequence']*=9
  with self.assertRaises(ValueError):self.normalize(c)
if __name__=='__main__':unittest.main()
