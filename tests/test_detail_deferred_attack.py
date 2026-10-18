import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('deferred_attack_cases', ROOT / 'scripts/verify-deferred-attack-detail.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class DeferredAttackGPU(unittest.TestCase):
    def test_shared_quantities_and_cast_landing_order(self):
        device = v.Cuda()
        try:
            rows = v.quantities(device, 'native') + v.verify(device, 'native')
        finally:
            device.close()
        self.assertEqual(len(rows), 18)
        for row in rows:
            with self.subTest(name=row['name']):
                self.assertTrue(row['passed'], row)
        # The full suite already includes legacy named-target phase tests.
        # They are selected by the standalone verifier, not repeated here.


if __name__ == '__main__':
    unittest.main()
