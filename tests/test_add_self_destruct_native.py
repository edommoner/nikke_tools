"""Final canonical queued hits remain valid when their source retires."""
import copy,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from world_add_self_destruct_native import fixtures,observe,verify


class AddSelfDestructNativeTests(unittest.TestCase):
    def test_all_original_shots_remain_and_inputs_methods_are_unchanged(self):
        from calculator.boss_pattern import BossScript
        methods={n:getattr(BossScript,n) for n in ('begin_frame','_add_attacks','_retire')}
        cases=fixtures();before=copy.deepcopy(cases)
        for case in cases:
            with self.subTest(case=case['name']):
                native,trace=observe(case);contract=verify(case,native)
                self.assertTrue(contract['verified']);self.assertEqual(contract['queued_shots'],case['hits']);self.assertEqual(trace,[])
                self.assertFalse(native['full_battle_validation']);self.assertFalse(native['gpu_supported'])
        self.assertEqual(cases,before)
        self.assertEqual(methods,{n:getattr(BossScript,n) for n in methods})

    def test_dropping_a_final_shot_or_delaying_retirement_fails_the_contract(self):
        case=fixtures()[1];native,_=observe(case)
        for change in ('drop','alive','death-event'):
            broken=copy.deepcopy(native);last=next(r for r in broken['frames'] if 'enemy_death' in r['events'])
            if change=='drop':last['queued']=[]
            elif change=='alive':last['alive']=True
            else:last['events'].remove('enemy_death')
            with self.subTest(change=change),self.assertRaises(AssertionError):verify(case,broken)




if __name__=='__main__':unittest.main()
