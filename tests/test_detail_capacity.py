import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('capacity_verifier',ROOT/'scripts/verify-capacity-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class CapacityTests(unittest.TestCase):
    def test_masks_cover_high_ids_without_overwriting_descriptor_fields(self):
        self.assertEqual(v.g.NE,256);self.assertEqual(v.g.MASK_WORDS,8)
        for name,p,script,expected in v.primitives():
            with self.subTest(name=name):
                self.assertLessEqual(len(p['effects']),v.g.NE)
                self.assertTrue(all(len(r)==v.g.EW for r in p['effects']))
                self.assertTrue(all(r[245:249]==[0]*4 for r in p['effects']))
                self.assertTrue(all(r[52:56]==[0]*4 for r in p['effects']))
    def test_overflow_fails_before_cuda(self):
        with self.assertRaises(v.g.UnsupportedDetail) as caught:
            v.c.oracle.program(v.c.oracle.characters(v.NAMES),v.fillers(257))
        self.assertIn('256',str(caught.exception))
    def test_rich_owned_profile_exceeds_old_capacity(self):
        compiled=v.t.a.evaluate({**v.rich_fixture(),'_compile_gpu_detail':True})
        self.assertEqual(len(compiled['program']['effects']),172)
    def test_high_ids_match_cpu_on_native_gpu(self):
        device=v.Cuda()
        try:rows=v.verify_primitives(device,'native')
        finally:device.close()
        self.assertTrue(rows);self.assertTrue(all(r['passed'] for r in rows),[r for r in rows if not r['passed']])
if __name__=='__main__':unittest.main()
