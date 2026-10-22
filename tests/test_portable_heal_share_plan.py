"""Plan literals catch lost links, wrong order, snapshot or capacity acceptance."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('heal_plan_probe',ROOT/'research/verify-heal-share-plan-short.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
class HealSharePlanTests(unittest.TestCase):
    def test_literal_oracle_rejects_changed_totals_links_portions_and_nested_state(self):
        entries,_=probe.prepare();self.assertEqual(len(entries),10)
        for name,words,domain in entries:
            expected=probe.native_reference(domain) if domain is not None else [64];block=expected+[0]*(probe.suite.OUTPUT-len(expected))
            if domain is None:probe.validate_rejection(block,name)
            else:self.assertEqual(probe.compare(block,domain),expected)
            for index in range(len(expected)):
                changed=list(block);changed[index]^=1
                with self.subTest(case=name,index=index),self.assertRaises(AssertionError):
                    if domain is None:probe.validate_rejection(changed,name)
                    else:probe.compare(changed,domain)
    def test_operation_order_boundaries_are_not_reassociated(self):
        self.assertNotEqual(.1*2/5,.1*(2/5));self.assertNotEqual(.1,(.1*3)/3)
        self.assertEqual(probe.CASES[5][-1][:3],[.04,.04,.02]);self.assertEqual(probe.CASES[6][-1][0],.1)
    def test_capacity_case_and_packed_word_count(self):
        entries,data=probe.prepare();self.assertEqual(len(data),4*(1+520*10))
        self.assertEqual(entries[7][1][0],512);self.assertIsNone(entries[8][2]);self.assertEqual(entries[9][1][0],513)
