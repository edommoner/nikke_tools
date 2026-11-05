"""Both real listeners keep their own thresholds and formation positions."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_mixed_group_cases import fixtures
from portable_mixed_group_contracts import verify
from portable_battle_attack_group_input import compile_battle
from world_battle_native_route_native import observe
class MixedGroupTests(unittest.TestCase):
    def test_static_inputs_use_both_real_listener_owners_without_cpu_traces(self):
        from calculator import timeline
        cases=fixtures();self.assertEqual(len(cases),20);self.assertEqual(len({c['name'] for c in cases}),20)
        for case in [c for c in cases if c['contract']['duration']==3]:
            with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU trace input')):
                p=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True));words,metadata=compile_battle(p,routing=case['routing'],group_history='compact')
            self.assertEqual(words[104402],3 if case['contract']['formation']==0 else 24)
            self.assertEqual(words[104403],1);self.assertFalse(metadata['real_prepared_input']['declared_attack_group_policy']['cpu_trace_used_as_gpu_input'])
    def test_native_battles_and_distinct_owner_thresholds(self):
        cases=fixtures()
        for index in (0,1,3,10,13):
            case=cases[index];n,_=observe(case);result=verify(case,n);self.assertTrue(result['verified'])
            if case['routing']=='all-logical-enemies':
                bad=copy.deepcopy(n);bad['notifications'][0]['owner']='벨로타'
                with self.assertRaises(AssertionError):verify(case,bad)
                bad=copy.deepcopy(n);bad['notifications'][0]['key'][0]='벨로타'
                with self.assertRaises(AssertionError):verify(case,bad)

if __name__=='__main__':unittest.main()
