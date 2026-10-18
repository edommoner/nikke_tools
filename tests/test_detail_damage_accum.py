import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('damage_accum_cases',ROOT/'scripts/verify-damage-accum.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class DamageAccumGPU(unittest.TestCase):
 def test_quantities_lifetimes_order_and_representative_squads(self):
  rows=m.verify('native');self.assertEqual(len(rows),12)
  for row in rows:
   with self.subTest(name=row['name']):self.assertTrue(row['passed'],row)
if __name__=='__main__':unittest.main()
