import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('typed_impact_witnesses',ROOT/'scripts/verify-typed-impacts-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class TypedImpactGPU(unittest.TestCase):
    def test_transport_and_migrated_landing_paths(self):
        device=v.Cuda()
        try:rows=[v.quantities(device,'native')]+v.squads(device,'native')
        finally:device.close()
        self.assertEqual(len(rows),3);self.assertTrue(all(r['passed'] for r in rows))
if __name__=='__main__':unittest.main()
