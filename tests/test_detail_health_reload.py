from detail_gpu import compile_effects,UnsupportedDetail
"""HP conversion and reload semantics use the independent upstream oracle."""
import sys,json,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('health_reload_regression',ROOT/'scripts/verify-health-reload-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class HealthReloadCompilerTests(unittest.TestCase):
 def test_special_values_remain_separate_from_generic_stat_routing(self):
  es=[v.E('HP conversion','buff','atk_from_hp_pct',2),v.E('fixed reload','buff','reload_time_fixed',.3),v.E('forced reload','instant','force_reload',0)]
  rows=compile_effects(v.oracle.characters(v.NAMES),[(e,v.NAMES[0]) for e in es])['effects']
  self.assertEqual([(q[1],q[241],q[242]) for q in rows],[(4,1,0),(4,0,1),(23,0,0)])
  for stat in ['atk_flat','enemy_def_down_pct','enemy_def_down_flat']:
   with self.assertRaises(UnsupportedDetail):compile_effects(v.oracle.characters(v.NAMES),[(v.E('internal field','buff',stat,1),v.NAMES[0])])
if __name__=='__main__':unittest.main()
