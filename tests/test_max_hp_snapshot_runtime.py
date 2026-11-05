import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('hp_snapshot_boundaries',ROOT/'scripts/verify-max-hp-snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from effect_runtime import CATALOG
class MaximumHPSnapshotRuntimeTests(unittest.TestCase):
 def test_reference_quantities_shared_activation_and_expiry(self):
  self.assertTrue(all(row['passed'] for row in m.independent(None,'native',True)))
  self.assertEqual(CATALOG.handlers['max_hp_snapshot'].resource_kind,'max_hp_snapshot')
 def test_unresolved_and_enemy_targets_reject(self):
  chars=m.v.characters(m.N)
  for target in ('target','allies_top_atk:1',['self','all_allies']):
   with self.subTest(target=target),self.assertRaises(m.g.UnsupportedDetail):m.g.compile_effects(chars,[(m.B('snapshot','max_hp_from_max_hp_pct',25,target),m.N[0])])
if __name__=='__main__':unittest.main()
