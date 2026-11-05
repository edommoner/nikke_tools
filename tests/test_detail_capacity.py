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
    def test_overflow_fails_before_execution(self):
        with self.assertRaises(v.g.UnsupportedDetail) as caught:
            v.c.oracle.program(v.c.oracle.characters(v.NAMES),v.fillers(257))
        self.assertIn('256',str(caught.exception))
if __name__=='__main__':unittest.main()
