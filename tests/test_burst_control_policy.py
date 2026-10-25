"""Independent native witnesses, bounded literal packing and full readback checks."""
import copy
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('burst_policy_test',ROOT/'research/verify-burst-control-policy-short.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
from portable_burst_control_specs import pack, WORDS

class BurstPolicyTests(unittest.TestCase):
    def test_native_decision_witnesses(self):
        rows={name:a.native_reference(d) for name,d in a.fixtures()}
        self.assertEqual(rows['delay-blocks-ready-alternative']['owner'],5)
        self.assertEqual(rows['delay-blocks-ready-alternative']['wait_mask'],0)
        self.assertEqual(rows['delay-blocks-ready-alternative']['action'],a.bits(2.))
        self.assertEqual(rows['delay-after-cooldown']['action'],a.bits(5.))
        self.assertEqual(rows['wait-blocks-ready-alternative']['wait_mask'],1)
        self.assertEqual(rows['wait-down-skipped']['owner'],1)
        self.assertEqual(rows['automatic-reserves-first']['owner'],5)
        self.assertEqual(rows['explicit-stage-allows-fallback']['owner'],1)
        self.assertEqual(rows['reentry-allows-fallback']['owner'],1)
        self.assertEqual(rows['empty-pattern-demotes']['owner'],1)
        self.assertEqual(rows['explicit-order-ignores-pattern']['owner'],1)
        self.assertEqual(rows['explicit-empty-cycle-blocks']['action'],a.bits(float('inf')))
        self.assertEqual(rows['explicit-empty-cycle-blocks']['prediction'],a.bits(-1.))
        self.assertEqual(rows['null-pattern-presence-allows-fallback']['owner'],1)
        self.assertEqual(rows['all-unavailable-retains-action']['action'],a.bits(4.))
        self.assertEqual(rows['ready-below']['owner'],1)
        self.assertEqual(rows['ready-exact']['owner'],0)
        self.assertEqual(rows['delay-below']['owner'],5)
        self.assertEqual(rows['delay-exact']['owner'],0)
        self.assertEqual(rows['wait-exact']['wait_mask'],1)
        self.assertEqual(rows['wait-above']['owner'],1)

    def test_literal_packing_is_pure_and_keeps_null_empty_and_boundaries(self):
        before=copy.deepcopy(a.fixtures())
        with patch.object(a,'native_reference',side_effect=AssertionError('Packing cannot call native')):
            rows,raw=a.prepare()
        self.assertEqual(len(raw),4+len(rows)*a.INPUT_WORDS*4)
        self.assertEqual(a.fixtures(),before)
        w=pack(a.NAMES,patterns={'one':None,'two':[],'three':[1,32,33,512],'four':'every:4294967295'})
        self.assertEqual(len(w),WORDS);self.assertEqual(w[30],1);self.assertEqual(w[36],2)
        self.assertEqual(w[62],0x80000001);self.assertEqual(w[63],1);self.assertEqual(w[77],1<<31)
        for kw in [dict(waits={'one':True}),dict(waits={'one':.49}),dict(waits={'one':3.1}),dict(delays={'one':float('nan')}),
            dict(delays={'unknown':1.}),dict(patterns={'one':[True]}),dict(patterns={'one':[513]}),dict(patterns={'one':'every:0'}),dict(patterns={'one':'every:4294967296'}),
            dict(sequence=[{}]*17),dict(sequence=[{'1':['one','one']}]),dict(sequence=[{'0':[]}])]:
            with self.subTest(kw=kw),self.assertRaises(ValueError):pack(a.NAMES,**kw)

    def test_full_readback_detects_control_numeric_and_padding_mutations(self):
        d=next(d for name,d in a.fixtures() if name=='delay-blocks-ready-alternative')
        w=a.expected(a.native_reference(d));a.compare(w,d)
        for at in range(a.OUTPUT_WORDS):
            bad=list(w);bad[at]^=1
            with self.subTest(at=at),self.assertRaises(AssertionError):a.compare(bad,d)

if __name__=='__main__':unittest.main()
