"""Native fractional credit, snapshot, weapon category and callback contracts."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
s=importlib.util.spec_from_file_location('fraction_test_suite',ROOT/'research/verify-world-fraction.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
class FractionContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={c['name']:c for c in suite.fixtures()};cls.observed={n:suite.inspect_native(c)[0] for n,c in cls.rows.items()}
 def samples(self,n,event=22):return [r for r in self.observed[n]['fractional_hits'] if r['owner']==0 and r['event']==event]
 def test_zero_and_unit_probabilities_leave_accumulator_absent(self):
  for name,frac in [('critical-clamp--100',0),('critical-clamp-200',1)]:
   self.assertTrue(all(r['fraction']==frac and r['fired']==frac and not r['created'] for r in self.samples(name)))
 def test_binary64_remainder_crosses_on_the_seventh_default_hit(self):self.assertEqual([r['fired'] for r in self.samples('fraction-crit_hit')[:7]],[0]*6+[1])
 def test_unit_probability_preserves_existing_fractional_remainder(self):
  rows=self.samples('critical-retains-remainder-at-unit-rate');first=next(i for i,r in enumerate(rows) if r['fraction']==1);self.assertTrue(all(r['after']==rows[first-1]['after'] for r in rows[first:]))
 def test_callback_does_not_change_the_current_pellet_snapshot(self):
  rows=self.samples('critical-callback-does-not-resample-same-shot');self.assertEqual(len({r['fraction'] for r in rows[:10]}),1);self.assertGreater(rows[10]['fraction'],rows[0]['fraction'])
 def test_auto_interleaves_critical_and_core_per_pellet(self):
  rows=[r for r in self.observed['pellets3-muzzles2-frozen-critical']['fractional_hits'] if r['owner']==0];self.assertEqual([r['event'] for r in rows[:12]],[22,23]*6)
 def test_charge_batches_critical_then_core(self):
  rows=[r for r in self.observed['charge-skill-crit_hit']['fractional_hits'] if r['owner']==0];self.assertEqual([r['event'] for r in rows[:6]],[22]*3+[23]*3)
 def test_normal_only_critical_does_not_enter_skill_mode(self):self.assertEqual(self.samples('skill-mode-excludes-normal-critical'),self.samples('charge-skill-crit_hit'))
 def test_native_add_routing_keeps_the_original_core_fraction(self):self.assertTrue(all(r['fraction']>0 for r in self.samples('core-kept-on-add-route',23)))
 def test_core_unit_probability_does_not_create_accumulator(self):self.assertTrue(all(r['fraction']==1 and r['fired']==1 and not r['created'] for r in self.samples('core-unit-probability',23)))
 def test_gpu_input_is_authored_not_observed_credit(self):
  c=copy.deepcopy(self.rows['fraction-crit_hit']);w=suite.compile_case(c)[0];c['fractional_hits']=[dict(fraction=1)];self.assertEqual(w,suite.compile_case(c)[0]);self.assertEqual(w[0],suite.L['WORLD_FRACTION_ABI']);self.assertEqual(w[suite.L['TARGET_COUNTER_INPUT_BASE']+6],17)
 def test_post_fire_delay_is_packed_without_sum_then_subtract(self):
  import struct
  from portable_charge_clock_specs import compile_clock
  c=self.rows['charge-normal-crit_hit'];words=compile_clock(c['combat']['weapons'],c['post_fire_delays']);self.assertEqual(words[4:6],list(struct.unpack('<II',struct.pack('<d',.215))))
 def test_real_static_normalizer_reads_native_delay_without_a_battle(self):
  from unittest.mock import patch
  from calculator import timeline
  from world_frame_native import authored_metadata,roster_names
  from portable_charge_clock_specs import normalize_static_clock
  c=self.rows['charge-normal-crit_hit'];names=roster_names(c)
  with patch.dict(timeline._NIKKE,authored_metadata(c)),patch.dict(timeline._DELAYS['_exceptions'],{},clear=True),patch.dict(timeline._DELAYS['_defaults_by_weapon_type'],{'AR':{'post_reload_delay':0}},clear=True),patch.object(timeline,'simulate',side_effect=AssertionError('CPU battle forbidden during normalization')):
   self.assertEqual(normalize_static_clock([dict(name=n,skill_levels={'1':10,'2':10,'3':10}) for n in names],c['base_atk'],{}),c['post_fire_delays'])
 def test_fraction_banks_follow_spawn_bank_without_overlap(self):
  L=suite.L;self.assertEqual(L['WORLD_FRACTION_STATE_BASE'],L['WORLD_SPAWN_TRACE_BASE']+4096*4);self.assertEqual(L['WORLD_FRACTION_HEAD_BASE'],L['WORLD_FRACTION_STATE_BASE']+5*8);self.assertLessEqual(L['WORLD_FRACTION_TRACE_BASE']+2048*8,L['WORLD_PERIODIC_OUTPUT_WORDS'])
if __name__=='__main__':unittest.main()
