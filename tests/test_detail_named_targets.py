import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('named_target_cases',ROOT/'scripts/verify-named-target-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class NamedAttackTargetGPU(unittest.TestCase):
 def test_shared_repetition_order_and_four_real_squads(self):
  device=v.Cuda()
  try:rows=v.phase_cases(device,'native')+v.real_cases(device,'native')
  finally:device.close()
  self.assertEqual(len(rows),8)
  for row in rows:
   with self.subTest(name=row['name']):self.assertTrue(row['passed'],row)
if __name__=='__main__':unittest.main()
