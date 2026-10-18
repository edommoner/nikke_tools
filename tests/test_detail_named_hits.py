import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('named_hit_cases',ROOT/'scripts/verify-named-hits.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class NamedHitsGPU(unittest.TestCase):
 def test_shared_named_hit_context_forced_slots_and_representative_squads(self):
  rows=m.verify('native');self.assertEqual(len(rows),11)
  for row in rows:
   with self.subTest(name=row['name']):self.assertTrue(row['passed'],row)
if __name__=='__main__':unittest.main()
