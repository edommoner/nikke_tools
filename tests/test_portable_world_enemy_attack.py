"""Native attack-field contracts and portable ABI admission boundaries."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
s=importlib.util.spec_from_file_location('enemy_attack_contract','research/verify-world-enemy-attack.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
class EnemyAttackContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={c['name']:c for c in suite.fixtures()};cls.native={n:suite.observe(c) for n,c in cls.rows.items()}
 def hits(self,n):return [h['damage'] for h in self.native[n]['hits']]
 def test_percent_state_does_not_invent_a_native_damage_multiplier(self):
  for target in ('boss','target','all_enemies'):self.assertEqual(self.hits('atk_pct-'+target),self.hits('enemy-attack-baseline'))
 def test_native_enemy_percent_also_affects_outgoing_get_buffs_query(self):
  self.assertTrue(all(x<y for x,y in zip(self.native['atk_pct-boss']['damage'],self.native['enemy-attack-baseline']['damage'])))
 def test_caster_based_field_reads_base_attack_and_preserves_sign(self):
  b=self.hits('enemy-attack-baseline');self.assertEqual(self.hits('atk_caster_based_pct-boss'),[x-100 for x in b]);self.assertEqual(self.hits('caster-flat-positive'),[x+100 for x in b]);self.assertEqual(self.hits('caster-flat-uses-base-not-buffed-caster'),[x-100 for x in b])
 def test_negative_attack_is_clamped_before_defense_and_minimum_damage(self):self.assertEqual(set(self.hits('caster-flat-clamped-below-zero')),{1})
 def test_field_is_frozen_once_for_all_five_victims_of_a_hit(self):
  self.assertEqual(self.hits('caster-flat-runtime-self_hp_above:99')[:5],self.hits('atk_caster_based_pct-boss')[:5]);self.assertEqual(self.hits('caster-flat-runtime-self_hp_above:99')[5:],self.hits('enemy-attack-baseline')[5:])
 def test_expired_field_stops_before_subsequent_hits(self):
  self.assertEqual(self.hits('caster-flat-expiry')[:10],self.hits('atk_caster_based_pct-boss')[:10]);self.assertEqual(self.hits('caster-flat-expiry')[10:],self.hits('enemy-attack-baseline')[10:])
 def test_all128_captured_receivers_are_native_owned(self):self.assertEqual(len(self.native['caster-flat-128-recipients']['enemy_attack_fields']),128)
 def test_late_wave_does_not_inherit_existing_field(self):self.assertEqual(self.native['caster-flat-no-late-wave-retarget']['enemy_attack_fields'][-1]['flat'],0)
 def test_gpu_input_contains_authored_program_not_native_results(self):
  c=copy.deepcopy(self.rows['atk_caster_based_pct-boss']);before=suite.compile_case(c)[0];c['native']={'attack':123456};self.assertEqual(before,suite.compile_case(c)[0]);self.assertEqual(before[0],suite.L['WORLD_ENEMY_ATTACK_ABI']);self.assertEqual(before[suite.L['TARGET_COUNTER_INPUT_BASE']+6],13)
 def test_attack_snapshot_does_not_overlap_periodic_packets(self):
  L=suite.L;self.assertEqual(L['WORLD_ENEMY_ATTACK_BASE'],L['WORLD_PERIODIC_HEAD_BASE']+16);self.assertLessEqual(L['WORLD_ENEMY_ATTACK_BASE']+128*2,L['WORLD_PERIODIC_OUTPUT_WORDS'])
if __name__=='__main__':unittest.main()
