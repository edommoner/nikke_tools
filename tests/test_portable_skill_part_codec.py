import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('part_codec',ROOT/'research/verify-skill-part-codec-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class PartCodecTests(unittest.TestCase):
    def test_all_words_and_boundary_neighbors_are_checked(self):
        for domain in m.CASES[:3]:
            b=m.expected_block(domain);self.assertEqual(m.compare(b,domain),m.native_reference(domain))
            for at in (1,3,m.BASE-1,m.BASE+domain[1]*2,m.BASE+4096,786416):
                changed=b[:];changed[at]^=1
                with self.subTest(case=domain[0],at=at),self.assertRaises(AssertionError):m.compare(changed,domain)
    def test_overflow_and_nonzero_partial_writes_reject(self):
        m.validate_rejection([64,0],'part-codec-reject-overflow')
        for block in ([0,0],[64,1]):
            with self.assertRaises(AssertionError):m.validate_rejection(block,'part-codec-reject-overflow')
