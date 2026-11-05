from detail_gpu import compile_effects,UnsupportedDetail
import sys,unittest,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('probability_regression',ROOT/'scripts/verify-probability-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class ProbabilityCompilerTests(unittest.TestCase):
 def test_literal_level_and_missing_probability_are_distinct(self):
  chars=v.oracle.characters(v.NAMES);effects=[v.E('literal','buff','atk_pct',1,condition=['prob:25']),v.E('level','buff','atk_pct',1,condition=['prob:{0}'],trigger_values={'10':50}),v.E('missing','buff','atk_pct',1,condition=['prob:{0}'])]
  rows=compile_effects(chars,[(e,v.NAMES[0]) for e in effects])['effects']
  self.assertEqual(rows[0][15:18],[26,0,.25]);self.assertEqual(rows[1][15:18],[26,0,.5]);self.assertEqual(rows[2][15:18],[25,0,0])
if __name__=='__main__':unittest.main()
