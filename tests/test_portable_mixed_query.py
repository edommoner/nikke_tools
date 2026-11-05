"""Mixed observations preserve native execution and reject independent faults."""
import copy
import random
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from portable_mixed_query_cases import fixtures
from portable_mixed_query_contracts import verify
from world_mixed_query_native import observe
from world_projectile_native import observe as plain_observe


class MixedQueryTests(unittest.TestCase):
    def test_full_native_trace_and_semantic_read_counts_preserved(self):
        for case in fixtures():
            with self.subTest(case=case['name']):
                plain_counts=[];actual_counts=[]
                def measured(observer,counts):
                    with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get, \
                         patch.object(BuffManager,'has_live_stat',autospec=True,side_effect=BuffManager.has_live_stat) as live, \
                         patch.object(random,'sample',side_effect=random.sample) as sample:
                        result=observer(case)
                        counts.extend([get.call_count,live.call_count,sample.call_count])
                        return result
                plain,trace=measured(plain_observe,plain_counts)
                native,recorded=measured(observe,actual_counts)
                self.assertTrue(verify(case,native)['verified'])
                for key in ('mixed_query','focus_aim','heal_share_events'):native.pop(key)
                self.assertEqual(native,plain)
                self.assertEqual(recorded,trace)
                self.assertEqual(actual_counts,plain_counts)

    def test_faults_are_detected(self):
        case=fixtures()[-1];native,_=observe(case)
        for fault in ('rng','cache','lazy','hp','damage','heal','parts','camera'):
            bad=copy.deepcopy(native)
            if fault=='rng':bad['mixed_query']['samples'][0]['after_sha256']='0'*64
            elif fault=='cache':next(q for q in bad['mixed_query']['queries'] if q['hit'])['sample_indices']=[0]
            elif fault=='lazy':bad['mixed_query']['samples'][1]['lazy']=True
            elif fault=='hp':bad['allies'][0]['hp']+=1
            elif fault=='damage':bad['projectile_shots'][0]['damage']+=1
            elif fault=='heal':bad['heal_share_events'].pop()
            elif fault=='parts':bad['actor_pools']['pools'][1][3]+=1
            else:bad['focus_aim'][0]['camera']=0
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,bad)


if __name__=='__main__':unittest.main()
