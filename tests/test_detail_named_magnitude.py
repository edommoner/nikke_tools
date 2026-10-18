import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('named_magnitude_cases',ROOT/'scripts/verify-named-magnitude.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class NamedMagnitudeGPU(unittest.TestCase):
 def test_independent_quantities_and_representative_squad_interactions(self):
  rows=m.verify('native');self.assertEqual(len(rows),9)
  for row in rows:
   with self.subTest(name=row['name']):self.assertTrue(row['passed'],row)
if __name__=='__main__':unittest.main()
