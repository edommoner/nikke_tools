import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('target_counter_witnesses',ROOT/'scripts/verify-target-counters-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class TargetCounterGPU(unittest.TestCase):
    def test_common_target_counter_and_autonomous_landings(self):
        device=v.Cuda()
        try:rows=v.quantities(device,'native')+v.squads(device,'native')
        finally:device.close()
        self.assertEqual(len(rows),18);self.assertTrue(all(r['passed'] for r in rows))
if __name__=='__main__':unittest.main()
