"""Composition must preserve each input and comparator without native/GPU calls."""
import array
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('regression_test_adapter',ROOT/'research/verify-world-regression-short.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)


class RegressionAdapterTests(unittest.TestCase):
    def test_rows_and_opaque_domains_keep_independent_comparators(self):
        domain=({'fixture':True},{'metadata':True})
        a=SimpleNamespace(suite=SimpleNamespace(INPUT=2,OUTPUT=3,inspect_native=Mock(return_value=({'battle':1},['trace']))),prepare=lambda:([('positive',[1,2],domain),('negative',[3,4],None)],array.array('I',[2,1,2,3,4]).tobytes()),compare=Mock(return_value={'complete':'native'}))
        with patch.object(adapter,'suite',SimpleNamespace(INPUT=2,OUTPUT=3)),patch.dict(adapter.ADAPTERS,{'test':a},clear=True):
            entries,data=adapter.prepare()
            self.assertEqual([(name,list(words),domain) for name,words,domain in entries],
                             [('test/positive',[1,2],('test',domain)),('test/negative',[3,4],None)])
            self.assertTrue(all(isinstance(words,array.array) and words.typecode=='I' for _,words,_ in entries))
            self.assertEqual(data,array.array('I',[2,1,2,3,4]).tobytes())
            self.assertEqual(adapter.native_reference(entries[0][2]),dict(battle={'battle':1},skill_trace=['trace']))
            self.assertEqual(adapter.compare([0],entries[0][2]),{'complete':'native'})
            a.compare.assert_called_once_with([0],domain)
            a.validate_rejection=Mock(side_effect=ValueError('Late error was never reached'))
            with self.assertRaisesRegex(ValueError,'never reached'):adapter.validate_rejection([64],'test/negative')
            a.validate_rejection.assert_called_once_with([64],'negative')
            a.suite.INPUT=99
            with self.assertRaisesRegex(ValueError,'wire strides'):adapter.prepare()

    def test_malformed_child_packing_is_rejected_before_execution(self):
        child=SimpleNamespace(suite=SimpleNamespace(INPUT=2,OUTPUT=3),prepare=lambda:([('bad',[1,2],None)],b'wrong'))
        with patch.object(adapter,'suite',SimpleNamespace(INPUT=2,OUTPUT=3)):
            with self.assertRaisesRegex(ValueError,'header mismatch'):adapter.combine({'test':child})
