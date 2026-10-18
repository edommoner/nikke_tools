import sys,unittest,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import compile_effects,UnsupportedDetail,run
from gpu_selector import Cuda,probe
spec=importlib.util.spec_from_file_location('probability_regression',ROOT/'scripts/verify-probability-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class ProbabilityCompilerTests(unittest.TestCase):
 def test_literal_level_and_missing_probability_are_distinct(self):
  chars=v.oracle.characters(v.NAMES);effects=[v.E('literal','buff','atk_pct',1,condition=['prob:25']),v.E('level','buff','atk_pct',1,condition=['prob:{0}'],trigger_values={'10':50}),v.E('missing','buff','atk_pct',1,condition=['prob:{0}'])]
  rows=compile_effects(chars,[(e,v.NAMES[0]) for e in effects])['effects']
  self.assertEqual(rows[0][15:18],[26,0,.25]);self.assertEqual(rows[1][15:18],[26,0,.5]);self.assertEqual(rows[2][15:18],[25,0,0])
 def test_nonfinite_probability_and_bad_accumulator_index_rejected(self):
  chars=v.oracle.characters(v.NAMES)
  with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(v.E('bad','buff','atk_pct',1,condition=['prob:nan']),v.NAMES[0])])
  p=compile_effects(chars,[(v.E('count','buff','atk_pct',1,condition=['prob:25']),v.NAMES[0])])
  with self.assertRaisesRegex(ValueError,'probability accumulator'):run(None,[p],[[.1,2,106,0,127,0,0,0]],[[1,1]],[{}])
class ProbabilityGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_accumulators_context_and_whole_squads(self):
  cases=v.verify(self.device,include_real=False)
  self.assertTrue(all(c['passed'] for c in cases),json.dumps([c for c in cases if not c['passed']],ensure_ascii=True))
if __name__=='__main__':unittest.main()
