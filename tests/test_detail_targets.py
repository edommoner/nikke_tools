import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import compile_effects
from gpu_selector import Cuda,probe
spec=importlib.util.spec_from_file_location('targets_regression',ROOT/'scripts/verify-targets-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class TargetCompilerTests(unittest.TestCase):
 def test_caster_weapon_mask_and_pinned_innate_b3(self):
  chars=v.oracle.characters(v.NAMES);chars[0]['burst_stage']='3'
  p=compile_effects(chars,[(v.E('cast','buff','atk_pct',1,'allies_burst_casted_burst3'),v.NAMES[0]),(v.E('weapon','buff','atk_pct',1,'allies_burst_casted_weapon:MG'),v.NAMES[0])])
  self.assertEqual(p['effects'][0][48],1|4|8);self.assertEqual(p['effects'][1][48],2|8)
class TargetGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_independent_membership_and_filtered_rank_squads(self):
  cases=v.verify(self.device,include_real=False)
  self.assertTrue(all(c['passed'] for c in cases),str([c for c in cases if not c['passed']]))
if __name__=='__main__':unittest.main()
