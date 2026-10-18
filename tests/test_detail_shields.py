"""Shield quantities must agree after consumption, refresh and callbacks."""
import importlib.util, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('shield_regression',ROOT/'scripts/verify-shield-lifecycle-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class ShieldGPUTests(unittest.TestCase):
    def test_authored_quantities_ordering_and_consumption_callbacks(self):
        device=v.Cuda()
        try: rows=v.verify(device,'native')
        finally: device.close()
        self.assertEqual(len(rows),21)
        self.assertTrue(all(r['passed'] for r in rows),[r for r in rows if not r['passed']])

if __name__=='__main__':unittest.main()
