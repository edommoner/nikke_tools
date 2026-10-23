"""Whole-shot packet observation preserves native execution and old24 results."""
import copy,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from portable_interrupt_aim_cases import fixtures as old_cases
from portable_aimed_packet_cases import fixtures
from portable_aimed_packet_contracts import verify
from world_aimed_packet_native import observe
from world_interrupt_aim_native import observe as old_observe
from world_reload_native import observe as native_without_shot_observer


class AimedPacketReferenceTests(unittest.TestCase):
    def test_prior24_native_results_traces_and_receipts_are_exact(self):
        for case in old_cases():
            with self.subTest(case=case['name']):
                plain,trace=old_observe(case);actual,recorded=observe(case)
                actual.pop('physical_packet_sets')
                self.assertEqual(actual,plain);self.assertEqual(recorded,trace)

    def test_full_native_execution_and_semantic_read_counts_are_preserved(self):
        for case in fixtures():
            counts=[[],[]]
            def measure(run,counts):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get, \
                     patch.object(BuffManager,'has_live_stat',autospec=True,side_effect=BuffManager.has_live_stat) as live, \
                     patch.object(random,'sample',side_effect=random.sample) as sample:
                    result=run(case);counts.extend([get.call_count,live.call_count,sample.call_count]);return result
            with self.subTest(case=case['name']):
                # Disable only the optional typed publication in this baseline:
                # its registry still cannot represent private interrupt actors.
                with patch.object(BuffManager,'publish_landing',lambda *args:None):plain,trace=measure(native_without_shot_observer,counts[0])
                actual,recorded=measure(observe,counts[1]);self.assertTrue(verify(case,actual)['verified'])
                for key in ('physical_packet_sets','interrupt_landings','projectile_shots','focus_aim'):actual.pop(key)
                self.assertEqual(actual,plain);self.assertEqual(recorded,trace);self.assertEqual(*counts)

    def test_packet_order_target_quantity_and_physical_counts_cannot_be_folded(self):
        case=fixtures()[9];native,_=observe(case)
        self.assertEqual((sum(s['pellets']*s['muzzles'] for s in native['physical_packet_sets']),sum(len(s['packets']) for s in native['physical_packet_sets'])),(36,72))
        for fault in ('order','target','damage','pellets','missing','hp'):
            bad=copy.deepcopy(native);row=bad['physical_packet_sets'][0]
            if fault=='order':row['packets'][0],row['packets'][1]=row['packets'][1],row['packets'][0]
            elif fault=='target':row['packets'][1]['target']=''
            elif fault=='damage':row['packets'][1]['damage']+=1
            elif fault=='pellets':row['pellets']*=2
            elif fault=='missing':row['packets'].pop()
            else:bad['allies'][0]['hp']+=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,bad)


if __name__=='__main__':unittest.main()
