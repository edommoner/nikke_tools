from detail_gpu import compile_effects,UnsupportedDetail,TD
import importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('time_regression',ROOT/'scripts/verify-time-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class TimeCompilerTests(unittest.TestCase):
 def test_lifetime_and_fractional_period_are_accepted(self):
  effects=[v.E('state','buff','atk_pct',1,duration=None,duration_values={'10':2},duration_scaling='stack_count',duration_scaling_ref='fuel',scaling='stack_count',scaling_ref='fuel'),v.E('pulse','instant','gauge_charge',1,event='every:0.25s',gauge_id='fuel')]
  p=compile_effects(v.oracle.characters(v.NAMES),[(e,v.NAMES[0]) for e in effects]);self.assertEqual(p['effects'][0][7],2);self.assertEqual(p['effects'][1][TD+1],.25)
 def test_bad_duration_and_nonpositive_period_are_rejected(self):
  for e in [v.E('bad','buff','atk_pct',1,duration_scaling='unknown'),v.E('bad','buff','atk_pct',1,event='every:0s')]:
   with self.assertRaises(UnsupportedDetail):compile_effects(v.oracle.characters(v.NAMES),[(e,v.NAMES[0])])
if __name__=='__main__':unittest.main()
