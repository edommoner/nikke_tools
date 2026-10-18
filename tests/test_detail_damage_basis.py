import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('damage_basis_cases',ROOT/'scripts/verify-damage-basis-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class DamageBasisGPU(unittest.TestCase):
 def test_common_quantities_and_five_real_active_squads(self):
  device=v.Cuda()
  try:rows=v.quantities(device,'native')+v.real_cases(device,'native')
  finally:device.close()
  self.assertEqual(len(rows),17)
  for row in rows:
   with self.subTest(name=row['name']):self.assertTrue(row['passed'],row)
if __name__=='__main__':unittest.main()
