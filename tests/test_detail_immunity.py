"""Immunity regression must exercise real consumption and nested refresh."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('immunity_regression',ROOT/'scripts/verify-immunity-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class ImmunityGPUTests(unittest.TestCase):
    def test_whole_squads_preserve_per_recipient_pools_and_callback_order(self):
        device=v.Cuda()
        try:rows=v.verify(device,'native',quick=False)
        finally:device.close()
        self.assertEqual(len(rows),54)
        self.assertTrue(all(r['passed'] for r in rows),[r for r in rows if not r['passed']])
        by={row['name']:row for row in rows}
        self.assertGreater(by['nested-harm-before-recharge-reset']['observed']['blocked'],0)
        self.assertEqual(by['full-immunity-does-not-spend-count-pool']['observed']['allowed'],0)

if __name__=='__main__':unittest.main()
