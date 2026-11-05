import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_specs import LIMITS as L,FIELDS as F,ABI
from portable_damage_specs import STATS
from portable_hp_attack_specs import STAT
class HPAttackContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  spec=importlib.util.spec_from_file_location('hp_attack_test_core',ROOT/'scripts/verify-portable-combat.py');cls.v=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.v)
  cls.cases=json.loads((ROOT/'tests/fixtures/portable-hp-attack.json').read_text())['cases']
 def test_no_legacy_stage_override_or_vector_collision(self):
  c=self.cases[0];before=copy.deepcopy(c);words,_=self.v.compile_case(c);d=L['DEFINITION_BASE']
  self.assertEqual((words[d+F['KIND']],words[d+F['STAT']]),(0,STAT));self.assertGreaterEqual(STAT,64)
  self.assertEqual([k for k,v in STATS.items() if v==STAT],['atk_from_hp_pct']);self.assertEqual(c,before)
  self.assertEqual((ABI,L['INPUT_WORDS'],L['OUTPUT_WORDS']),(0x50455673,86016,159744))
 def test_late_ranked_targets_do_not_join_mapped_query_cache(self):
  c=next(c for c in self.cases if c['name'].startswith('hp-attack-fresh-rank-'));w,_=self.v.compile_case(c);flag=w[L['RECIPIENT_BASE']+7]
  self.assertNotEqual(flag>>4,0);self.assertEqual(flag&4,0)
 def test_native_order_and_rank_observation(self):
  from portable_hp_attack_oracle import observe
  for prefix in ('hp-attack-order-0-','hp-attack-fresh-rank-0-'):
   c=next(c for c in self.cases if c['name'].startswith(prefix));r=observe(c)
   self.v.contains(r['queries'],c['expected_queries'],c['name'])
   if 'order' in prefix:self.assertEqual(r['native_observations'][0]['flat'],[1]*5)
 def test_malformed_payloads_exercise_admission_without_mutating_fixture(self):
  from portable_hp_attack_validation import rejection_programs
  before=copy.deepcopy(self.cases);bad,expected=rejection_programs(self.cases,self.v.compile_case)
  self.assertEqual(len(bad),23);self.assertEqual([r['status'] for r in expected],[64]*21+[16]*2);self.assertEqual(self.cases,before)
if __name__=='__main__':unittest.main()
