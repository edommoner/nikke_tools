"""CPU prerequisites for the actual composite heal_split recipient surface."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,detail_gpu,portable_runtime
from calculator import timeline
from portable_heal_share_target_cases import fixtures
from portable_heal_share_contracts import verify
from world_heal_share_native import observe
from world_projectile_native import observe as plain_observe
spec=importlib.util.spec_from_file_location('heal_targets_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class HealShareTargetTests(unittest.TestCase):
    def test_literal_cases_forbid_gpu_and_packing(self):
        def forbidden(*a,**kw):raise AssertionError('Packing/GPU forbidden')
        with patch.object(timeline,'simulate',forbidden):cases=fixtures()
        self.assertEqual(len(cases),6);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case=case['name']):self.assertTrue(verify(case,observe(case)[0])['verified'])
        self.assertEqual(cases,before)

    def test_observer_preserves_full_native_state_and_trace(self):
        for case in fixtures():
            native,trace=observe(case);plain,plain_trace=plain_observe(case);native.pop('heal_share_events')
            with self.subTest(case=case['name']):self.assertEqual(native,plain);self.assertEqual(trace,plain_trace)

    def test_duplicate_self_wrong_rank_and_wrong_owner_are_detected(self):
        for index,weights in ((1,[(0,2),(1,1)]),(4,[(0,1),(1,1),(3,1)]),(5,[(0,1),(1,1),(2,1)])):
            case=fixtures()[index];native,_=observe(case);changed=copy.deepcopy(native)
            next(e for e in changed['heal_share_events'] if e['kind']=='plan')['weights']=weights
            with self.subTest(case=case['name']),self.assertRaises(AssertionError):verify(case,changed)

    def test_reassociated_hp_percentage_is_rejected_without_tolerance(self):
        case=fixtures()[3];native,_=observe(case);self.assertTrue(verify(case,native)['verified'])
        self.assertEqual(native['allies'][3]['hp_pct'],55.00000000000001)
        changed=copy.deepcopy(native);changed['allies'][3]['hp_pct']=55.0
        with self.assertRaises(AssertionError):verify(case,changed)


if __name__=='__main__':unittest.main()
