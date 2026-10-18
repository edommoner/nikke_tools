import importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('hp_snapshot_oracle',ROOT/'scripts/verify-max-hp-snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class MaximumHPSnapshotTests(unittest.TestCase):
 def test_shared_squads_and_independent_quantities(self):
  rows=m.verify('native');self.assertEqual(len(rows),8)
  self.assertTrue(all(row['passed'] for row in rows),json.dumps([row for row in rows if not row['passed']],ensure_ascii=True))
if __name__=='__main__':unittest.main()
