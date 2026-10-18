import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('resource_limit_witnesses', ROOT / 'scripts/verify-resource-limits-detail.py')
v = importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


class ResourceLimitsGPU(unittest.TestCase):
    def test_shared_quantities_and_nested_squads(self):
        device = v.Cuda()
        try:rows = v.quantities(device, 'native') + v.squad_cases(device, 'native')
        finally:device.close()
        self.assertEqual(len(rows), 16)
        for row in rows:
            with self.subTest(name=row['name']):self.assertTrue(row['passed'], row)
        # The full suite already has the legacy gauge primitives; the
        # standalone verifier selects those without adding another copy here.
