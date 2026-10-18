import importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import compile_effects,UnsupportedDetail
from gpu_selector import Cuda,probe
spec=importlib.util.spec_from_file_location('stackops_regression',ROOT/'scripts/verify-stackops-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class StackOperationCompilerTests(unittest.TestCase):
 def test_definition_reference_raw_duration_and_polarity(self):
  owner=v.NAMES[0];chars=v.oracle.characters(v.NAMES)
  effects=[(v.E('init','instant','buff_stack_init',3,event='burst_cast',target_effect='state'),owner),(v.E('state','buff','atk_pct',10,duration=1,duration_values={'10':5},max_stack=3,polarity='beneficial_irremovable'),owner)]
  p=compile_effects(chars,effects)
  self.assertEqual(p['effects'][0][215],1)
  self.assertEqual(p['effects'][1][7],1);self.assertEqual(p['effects'][1][208],1);self.assertEqual(p['effects'][1][209],1)
 def test_malformed_reference_and_buff_tick_are_rejected(self):
  chars=v.oracle.characters(v.NAMES);owner=v.NAMES[0]
  for effect in [v.E('invalid','instant','buff_stack_add',1,target_effect=[]),v.E('invalid','buff','atk_pct',1,tick_interval=1)]:
   with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(effect,owner)])
class StackOperationGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_independent_state_and_complete_squads(self):
  cases=v.verify(self.device,include_real=False)
  self.assertTrue(all(c['passed'] for c in cases),json.dumps([c for c in cases if not c['passed']],ensure_ascii=True))
if __name__=='__main__':unittest.main()
