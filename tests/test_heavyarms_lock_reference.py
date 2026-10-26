"""Keep partial named-marker evidence from becoming full Lock On certification."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu as cli
import world_heavyarms_lock_native as observer
from portable_heavyarms_lock_cases import fixtures,factory
from portable_heavyarms_lock_contracts import verify

class HeavyarmsLockReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures()
        with cli.forbid_gpu():cls.results=[observer.observe(c) for c in cls.cases]
    def test_full_source_profiles_and_native_transparency(self):
        for case,(native,trace) in zip(self.cases,self.results,strict=True):
            with self.subTest(case=case['name']),cli.forbid_gpu():
                result=verify(case,native);baseline,shots=factory().native_reference(case['body'])
                actual=dict(native);actual.pop('heavyarms_lock')
                self.assertEqual((actual,trace),(baseline,shots));self.assertTrue(result['reference_model_gap']);self.assertFalse(result['gpu_supported'])
    def test_missing_carrier_stack_recipient_query_or_removal_is_rejected(self):
        case=self.cases[0];source=self.results[0][0]
        for fault in ('stack','recipient','query','removal','original','support'):
            native=copy.deepcopy(source);o=native['heavyarms_lock'];activation=next(e for e in o['events'] if e['kind']=='activate')
            if fault=='stack':activation['state']['carriers'][0]['stack']=6
            elif fault=='recipient':activation['state']['carriers'][0]['targets']=['__enemy__:invented']
            elif fault=='query':activation['state']['diagnostic_queries']['boss']=False
            elif fault=='removal':next(e for e in o['events'] if e['kind']=='remove')['state']=copy.deepcopy(activation['state'])
            elif fault=='original':o['original_definitions'][4]['name']='modified definition'
            else:o['spatial_selection_verified']=True
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,native)
    def test_changed_battle_under_observer_is_rejected(self):
        source=factory();original=source.native_reference;calls=[]
        def changed(body):
            native,trace=original(body);calls.append(1)
            if len(calls)==1:native=dict(native,observer_changed_battle=True)
            return native,trace
        source.native_reference=changed
        with cli.forbid_gpu(),patch.object(observer,'factory',return_value=source),self.assertRaisesRegex(AssertionError,'changed complete native'):
            observer.observe(self.cases[0])
    def test_registered_contract_retains_model_gap(self):
        from portable_reference import REFERENCES
        from portable_model_gap_audit import verify as gaps
        self.assertIn('heavyarms-lock-marker-native',REFERENCES)
        lock=gaps(ROOT)['missing_stats']['lock_on']
        self.assertIn('generic named carriers',lock['consumer_search_scope']);self.assertFalse(lock['dedicated_spatial_selection_verified']);self.assertFalse(lock['target_count_extension_verified'])

if __name__=='__main__':unittest.main()
