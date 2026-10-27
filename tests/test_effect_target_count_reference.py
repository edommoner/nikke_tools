"""Actual original25 battle observations retain exact two-shot query lifetime."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_effect_target_count_cases import fixtures
import world_effect_target_count_native as observer
from portable_effect_target_count_contracts import verify
from portable_heavyarms_lock_cases import factory

class TargetCountReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.results=[observer.observe(c) for c in cls.cases]
    def test_complete_profiles_and_two_shot_expiry_on_actual_events(self):
        self.assertEqual(len(self.cases),4)
        for case,(native,trace) in zip(self.cases,self.results,strict=True):
            with self.subTest(case=case['name']):
                r=verify(case,native);self.assertTrue(r['named_target_count_query_verified']);self.assertFalse(r['selection_consumer_connected']);self.assertFalse(r['gpu_supported'])
                baseline,shots=factory().native_reference(case['body']);actual=dict(native);actual.pop('effect_target_count')
                self.assertEqual((actual,trace),(baseline,shots))
    def test_corrupted_before_query_missing_activation_and_false_gpu_support_fail(self):
        case=next(c for c in self.cases if c['body']['duration']==30)
        source=self.results[self.cases.index(case)][0]
        for fault in ('before','activation','shot','gpu','definition'):
            bad=copy.deepcopy(source);r=bad['effect_target_count']
            if fault=='before':next(e for e in r['events'] if e['kind']=='consume')['before']['additional_targets']=False
            elif fault=='activation':r['events']=[e for e in r['events'] if e['kind']!='activate']
            elif fault=='shot':r['events'].remove(next(e for e in r['events'] if e['kind']=='consume' and e['before']['capacity']==15))
            elif fault=='gpu':r['gpu_supported']=True
            else:r['original_definitions'].pop()
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,bad)
    def test_changed_complete_battle_is_not_hidden_by_query_observer(self):
        source=factory();original=source.native_reference;calls=[]
        def changed(body):
            result,trace=original(body);calls.append(1)
            return (dict(result,changed_by_query=True) if len(calls)==1 else result),trace
        source.native_reference=changed
        with patch.object(observer,'factory',return_value=source),self.assertRaisesRegex(AssertionError,'changed complete native'):
            observer.observe(self.cases[0])

if __name__=='__main__':unittest.main()
