"""A queued sequential skill cannot read membership after physical clear."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from world_lock_delivery_order_native import observe_order

class DeliveryOrderTests(unittest.TestCase):
    def test_original_gauge_hit_budget_and_fire_order_need_immutable_snapshot(self):
        result=observe_order()
        self.assertEqual(len(result['shots']),2);self.assertFalse(result['delivery_policy_installed'])
        for shot in result['shots']:
            events=[e for e in result['events'] if e['time']==shot['time']]
            self.assertEqual([e['event'] for e in events],['on_attack','full_charge_fire','hit_count:오토 파이어 2','hit_count:오토 파이어 2','hit_count','hit_count'])
            self.assertEqual([e['gauge'] for e in events],[2.,2.,2.,2.,0.,0.])
            self.assertEqual(len(shot['handles']),2);self.assertIn(shot['time'],result['clears'])
        from portable_heavyarms_lock_cases import source_definitions
        for row in result['original_definitions']:self.assertEqual(row['definition'],source_definitions()[row['index']])

if __name__=='__main__':unittest.main()
