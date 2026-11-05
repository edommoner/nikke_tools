"""Native reload ordering, fixed-value semantics and declarative GPU input packing."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
import engine_worker,portable_backend
from world_reload_cases import fixtures
from world_reload_native import observe
from portable_reload_specs import pack,STAT,WORDS
from portable_specs import LIMITS as L,FIELDS as F
s=importlib.util.spec_from_file_location('reload_test_suite',ROOT/'research/verify-world-reload.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
class ReloadContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows={c['name']:c for c in fixtures()};cls.observed={n:observe(c) for n,c in cls.rows.items()};cls.native={n:value[0] for n,value in cls.observed.items()}
 def test_all_legacy_native_fingerprints_from_existing_observations(self):
  expected=json.loads((ROOT/'tests/fixtures/portable-reload-native-baseline.json').read_text())['native_fingerprints']
  spec=importlib.util.spec_from_file_location('reload_native_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
  self.assertEqual(set(expected),set(self.observed));self.assertEqual(len(expected),46)
  for name,(native,trace) in self.observed.items():self.assertEqual(cross.digest(dict(battle=native,skill_trace=trace)),expected[name],name)
 def row(self,name):return self.rows['reload-'+name]
 def native_case(self,name):return self.native['reload-'+name]
 def first_start(self,name):return next(r for r in self.native_case(name)['reload_events'] if r['kind']=='start' and r['owner']==0)
 def test_fixed_time_chooses_maximum_without_base_or_sum(self):
  a=self.first_start('max-not-sum-or-base');b=self.first_start('later-shorter-fixed');self.assertEqual(a['until'],a['time']+.4);self.assertEqual(a,b)
 def test_bare_presence_does_not_set_zero_seconds(self):
  a=self.first_start('bare-fixed-falls-back');self.assertEqual(a['until'],a['time']+.6)
 def test_skill_level_values_are_absolute_times(self):
  a=self.first_start('level-fixed');self.assertEqual(a['until'],a['time']+.0004)
 def test_speed_buff_cannot_shorten_fixed_time(self):
  a=self.first_start('fixed-ignores-speed-buffs');self.assertEqual(a['until'],a['time']+.4)
 def test_finite_expiry_does_not_reschedule_started_reload(self):
  a=self.first_start('expiry-does-not-reschedule');self.assertEqual(a['until'],a['time']+.7);self.assertGreater(a['until'],.4)
 def test_direct_fixed_query_ignores_later_runtime_hp_condition(self):
  for duration in (-1,.9):
   a=self.first_start('fixed-ignores-later-condition-'+str(duration));self.assertGreater(a['time'],.3);self.assertEqual(a['until'],a['time']+.3)
 def test_force_cancels_hold_before_later_alias_condition(self):
  n=self.native_case('force-cancels-before-later-raw-alias');notes=n['manual_control']['notifications'];self.assertEqual(notes[0]['event'],'charge_hold:0.1');self.assertEqual(notes[1]['event'],'charge_hold:0.10');self.assertEqual(notes[1]['full_time'],-1.);self.assertFalse(any(c['name']=='must-not-trigger' for c in n['named_state']['allied_carriers']))
 def test_force_while_reloading_is_not_a_restart(self):
  rows=[r for r in self.native_case('already-reloading-not-restarted')['reload_events'] if r['owner']==0];self.assertGreater(sum(r['kind']=='force' for r in rows),1);self.assertEqual(sum(r['kind']=='start' for r in rows),1)
 def test_full_reload_callback_is_synchronous_before_finish_return(self):
  rows=[r for r in self.native_case('full-reload-callback-restarts')['reload_events'] if r['owner']==0];self.assertEqual([r['kind'] for r in rows[:5]],['force','start','force','start','finish']);self.assertEqual(rows[4]['until'],rows[3]['until']);self.assertEqual(rows[4]['ammo'],0)
 def test_clip_refills_start_next_reload_before_finish_returns(self):
  rows=[r for r in self.native_case('clip-three-refills')['reload_events'] if r['owner']==0];self.assertEqual([r['kind'] for r in rows[:6]],['force','start','start','finish','start','finish']);self.assertEqual(rows[2]['ammo'],2);self.assertEqual(rows[4]['ammo'],4)
 def test_physical_mode_callback_and_between_frame_use_distinct_reload_bases(self):
  a=self.first_start('mode-context-on_attack');b=self.first_start('mode-context-every:0.2s');self.assertEqual(a['until'],a['time']+.9);self.assertEqual(b['until'],b['time']+.6)
 def test_explicit_negative_budget_is_disabled_rather_than_unlimited(self):
  for kind in ('fixed','force','ordinary-buff','ordinary-ammo'):
   c=self.row('explicit-negative-budget-'+kind);w,_,_=suite.compile_case(c);self.assertEqual(w[L['DEFINITION_BASE']+F['BUDGET']],0)
 def test_literal_value_presence_and_force_identity_have_distinct_flags(self):
  w=pack([dict(type='buff',stat='reload_time_fixed'),dict(type='buff',stat='reload_time_fixed',fixed_value=0),dict(type='instant',stat='force_reload')]);self.assertEqual(w[8:11],[0,1,2]);self.assertEqual(len(w),WORDS)
 def test_packer_does_not_execute_native_or_gpu_battles(self):
  from calculator import timeline
  def stop(*a,**kw):raise AssertionError('Unexpected execution while packing')
  with patch.object(timeline,'simulate',stop),patch.object(timeline.CharState,'tick',stop),patch.object(portable_backend,'execute',stop),patch.object(portable_backend,'build',stop):w,_,_=suite.compile_case(self.row('fixed-0.2'))
  self.assertEqual(len(w),104400);self.assertEqual(w[0],L['WORLD_RELOAD_ABI']);self.assertEqual(w[L['TARGET_COUNTER_INPUT_BASE']+6],22);self.assertEqual(w[L['DEFINITION_BASE']+F['STAT']],STAT)
 def test_output_observations_are_not_packed(self):
  c=copy.deepcopy(self.row('fixed-0.2'));a=suite.compile_case(c)[0];c['reload_events']=[dict(time=-999,until=1)];c['observed_reload_until']=[0]*5;self.assertEqual(a,suite.compile_case(c)[0])
 def test_real_catalog_pair_has_not_been_rewritten(self):
  rows=[c for c in self.rows.values() if c['name'].startswith('reload-catalog-')];self.assertEqual(len(rows),2);self.assertEqual(sum(e.get('stat')=='force_reload' for c in rows for e in c['effects']),2)
 def test_all_authored_cases_pack_consistently(self):
  for c in self.rows.values():
   w,m,b=suite.compile_case(c);self.assertEqual(len(w),L['WORLD_RELOAD_INPUT_WORDS'])
 def test_new_output_layout_reaches_build_without_a_gpu_execution(self):
  import struct
  data=struct.pack('<I',1)+bytes(L['WORLD_RELOAD_INPUT_WORDS']*4)
  for size in (655360,786432):
   with patch.object(portable_backend,'build',side_effect=RuntimeError('build stopped before GPU')) as build:
    with self.assertRaisesRegex(RuntimeError,'build stopped before GPU'):portable_backend.execute(suite.SOURCE,'portableEvents',data,L['WORLD_RELOAD_INPUT_WORDS'],size)
    build.assert_called_once()
 def test_gap_output_layouts_still_reject_before_build(self):
  import struct
  for size in (524289,655359,655361,786431,786433):
   with patch.object(portable_backend,'build',side_effect=AssertionError('must not build')) as build:
    with self.assertRaisesRegex(ValueError,'word strides'):portable_backend.execute(suite.SOURCE,'portableEvents',struct.pack('<I',1),L['WORLD_RELOAD_INPUT_WORDS'],size)
    build.assert_not_called()
 def test_capacity_fails_instead_of_truncating_definitions(self):
  with self.assertRaises(ValueError):pack([{}]*257)
if __name__=='__main__':unittest.main()
