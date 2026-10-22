import importlib.util,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('factor_probe',ROOT/'research/verify-damage-factors-short.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
class DamageFactorsTests(unittest.TestCase):
    def test_literal_main_and_part(self):
        self.assertEqual(probe.native_reference(probe.CASES[1]),[0]+probe.bits(2500.)+probe.bits(4500.))
        self.assertEqual(probe.native_reference(probe.CASES[5]),[0]+probe.bits(0.)+probe.bits(200.))
        self.assertEqual(probe.native_reference(probe.CASES[6]),[0]+probe.bits(0.)+probe.bits(200.))
    def test_oracle_rejects_each_changed_word_and_extra_output(self):
        entries,data=probe.prepare();self.assertEqual(len(data),4*(1+18*len(entries)))
        for _,_,domain in entries:
            expected=probe.native_reference(domain);block=expected+[0]*4
            self.assertEqual(probe.compare(block,domain),expected)
            for index in range(len(block)):
                changed=list(block);changed[index]^=1
                with self.subTest(case=domain[0],index=index),self.assertRaises(AssertionError):probe.compare(changed,domain)
    def test_order_and_no_ratio_recovery(self):
        f=probe.CASES[3][1]
        expected=probe.native_reference(probe.CASES[3])
        reassociated=(f[0]/100.)*(f[1]*f[2]*f[3]*f[4]*f[5]*f[6])
        self.assertNotEqual(expected[1:3],probe.bits(reassociated))
        self.assertNotEqual(expected[3:],probe.bits(struct.unpack('<d',struct.pack('<II',*expected[1:3]))[0]*(f[7]/f[2])*(f[8]/f[4])))
