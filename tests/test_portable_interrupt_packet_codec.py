import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('interrupt_codec',ROOT/'research/verify-interrupt-packet-codec-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class InterruptPacketCodecTests(unittest.TestCase):
    def test_all_rotations_and_crossword_boundaries(self):
        for c in m.CASES[:128]:
            r=m.encode(c);bits=sum(word<<(32*i) for i,word in enumerate(r[6:34]))
            self.assertEqual([(bits>>(7*i))&127 for i in range(128)],c['order'])
            self.assertEqual(r[2:6],[0xffffffff]*4);self.assertEqual(r[34:],[c['low'],c['high'],4,m.TAG|2])
    def test_last_slot_stays_before_payload(self):
        r=m.encode(m.case('last',[0]*0+[127]))
        self.assertEqual(r[6],127);self.assertEqual(r[34],0)
        self.assertEqual(127*7+6,895);self.assertEqual(895//32,27)
    def test_whole_output_and_rejections_are_observed(self):
        entries,data=m.prepare();self.assertEqual(len(data),4*(1+len(entries)*136))
        for name,_,c in entries:
            original=m.BY_NAME[name];b=m.expected_block(original)
            check=(lambda v:m.compare(v,c)) if c else (lambda v:m.validate_rejection(v,name))
            check(b)
            for at in ((0,7,8,41,42,43,44,45,46,64,191,255,m.suite.OUTPUT-1) if original['name'] in ('rotate-0','reuse-direct','bad-count','mutate-6') else ()):
                changed=b[:];changed[at]^=1
                with self.subTest(case=name,word=at),self.assertRaises(AssertionError):check(changed)
    def test_reuse_clears_old_count_membership_and_suffix(self):
        for name in ('reuse-empty','reuse-tail','reuse-direct'):
            c=m.BY_NAME['interrupt-codec-'+name];self.assertTrue(c['reuse']);self.assertEqual(m.expected_block(c)[8:46].tolist(),m.encode(c))
