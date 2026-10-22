"""Lazy membership and binary64 operation order before GPU heal sharing."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from calculator import timeline
from portable_heal_share_extra_cases import fixtures
from portable_heal_share_contracts import verify
from world_heal_share_native import observe
from world_projectile_native import observe as plain_observe
spec=importlib.util.spec_from_file_location('heal_extra_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class HealShareExtraReferenceTests(unittest.TestCase):
    def test_eight_literal_contracts_forbid_packing_and_gpu(self):
        def forbidden(*a,**kw):raise AssertionError('Battle/packing forbidden')
        with patch.object(timeline,'simulate',forbidden):cases=fixtures()
        self.assertEqual(len(cases),8);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case=case['name']):self.assertTrue(verify(case,observe(case)[0])['verified'])
        self.assertEqual(cases,before)

    def test_all_existing_native_state_and_trace_remain_identical(self):
        for case in fixtures():
            with self.subTest(case=case['name']):
                plain,trace=plain_observe(case);native,observed_trace=observe(case)
                native.pop('heal_share_events');self.assertEqual(native,plain);self.assertEqual(observed_trace,trace)

    def test_reassociated_division_or_single_recipient_division_is_detected(self):
        cases=fixtures()
        for case,wrong in ((cases[-2],.1*(2/5)),(cases[-1],(.1*3)/3)):
            native,_=observe(case);correct=case['contract']['portion_sequence'][0][1]
            self.assertNotEqual(wrong,correct)
            changed=copy.deepcopy(native)
            next(r for r in changed['heal_share_events'] if r['kind']=='portion-call')['amount']=wrong
            with self.subTest(case=case['name']),self.assertRaises(AssertionError):verify(case,changed)

    def test_lazy_plan_recalculation_or_distinct_carrier_weight_loss_is_rejected(self):
        cases=fixtures()
        for index in (0,2,5):
            case=cases[index];native,_=observe(case);changed=copy.deepcopy(native)
            plan=next(r for r in changed['heal_share_events'] if r['kind']=='plan')
            plan['weights']=plan['weights'][1:]
            with self.subTest(case=case['name']),self.assertRaises(AssertionError):verify(case,changed)


if __name__=='__main__':unittest.main()
