"""Support witnesses cannot pass with missing casts, reentry, or an absent actor."""
import copy,hashlib,importlib.util,json,sys,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('support_contract_test',ROOT/'research/verify-original-catalogue-support.py')
support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)

class SupportContractTests(unittest.TestCase):
    pass


    def test_burst_witness_rejects_missing_or_reordered_reentry_and_owner(self):
        for name,expected in support.COHORT.items():
            trace=[dict(event=event,owner=owner) for event,owner in expected['casts']]
            support.verify_casts(name,trace)
            for fault in ('missing','owner','stage','order'):
                bad=copy.deepcopy(trace)
                if fault=='missing':bad.pop(0)
                elif fault=='owner':bad[0]['owner']=4
                elif fault=='stage':bad[0]['event']=3
                else:bad[:2]=reversed(bad[:2])
                with self.subTest(name=name,fault=fault),self.assertRaises(AssertionError):support.verify_casts(name,bad)

    def test_native_witness_rejects_uncharged_party_wrong_stage_and_no_own_shots(self):
        for name,expected in support.COHORT.items():
            native=dict(burst_controls=dict(ticks=[dict(stages=[expected['stage']],cycles=1)]),coordinate_typed_weapon=dict(attacks=[dict(owner=0)]))
            self.assertIs(support.verify_native(dict(name=name),native),native)
            for fault in ('cycle','stage','shots'):
                bad=copy.deepcopy(native)
                if fault=='cycle':bad['burst_controls']['ticks'][0]['cycles']=0
                elif fault=='stage':bad['burst_controls']['ticks'][0]['stages'][0]=3
                else:bad['coordinate_typed_weapon']['attacks']=[dict(owner=1)]
                with self.subTest(name=name,fault=fault),self.assertRaises(AssertionError):support.verify_native(dict(name=name),bad)

    def test_reentry_requires_the_shared_runtime_reentry_event(self):
        name=next(n for n in support.COHORT if '티아' in n)
        trace=[dict(event=e,owner=o) for e,o in support.COHORT[name]['casts']]
        self.assertEqual(trace[1],dict(event=7,owner=3))
        trace[1]['event']=1
        with self.assertRaises(AssertionError):support.verify_casts(name,trace)
        self.assertIn('stage+(s.reentrySlot != 0 ? 6 : 0)',(ROOT/'gpu/combat_runtime.slang').read_text())



if __name__=='__main__':unittest.main()
