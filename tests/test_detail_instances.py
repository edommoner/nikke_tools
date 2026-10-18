import importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from gpu_selector import Cuda,probe
spec=importlib.util.spec_from_file_location('instances_regression',ROOT/'scripts/verify-instances-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class ActiveInstanceGPUTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  status=probe()
  if not status['available']:raise unittest.SkipTest(status['reason'])
  cls.device=Cuda()
 @classmethod
 def tearDownClass(cls):cls.device.close()
 def test_partial_instances_and_independent_full_squads(self):
  cases=v.verify(self.device)
  self.assertTrue(all(c['passed'] for c in cases),json.dumps([c for c in cases if not c['passed']],ensure_ascii=True))
if __name__=='__main__':unittest.main()
