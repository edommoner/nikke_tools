"""Saved real CPU groups reject lost/duplicated notices and invented hits."""
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_moving_group_contracts import verify

class MovingGroupEventTests(unittest.TestCase):
    def setUp(self):
        self.rows=json.loads((ROOT/'tests/fixtures/moving-group-native-events-v1.json').read_text())['cases']
    def check(self,row):
        case=dict(original_run={},group_contract=row['group_contract'])
        # Isolate event-audit faults; the whole physical/motion contract is
        # independently exercised by CLI native preflight and Metal compare.
        with patch('portable_moving_typed_contracts.verify',return_value={}):return verify(case,row['native'])
    def test_saved_positive_outside_and_new_generation_event_sets(self):
        results=[self.check(row) for row in self.rows]
        self.assertEqual([r['qualifying_groups'] for r in results],[9,0,17])
        self.assertEqual([r['original_child_landings'] for r in results],[27,0,51])
        self.assertTrue(any(h[2]>1 for g in self.rows[2]['native']['groups'] for h in g['targets'] if h[0]==5))
    def test_corrupted_receipts_fail_instead_of_becoming_empty_coverage(self):
        for fault in ('missing-notice','duplicate-target','wrong-child','invented-outside-hit'):
            row=copy.deepcopy(self.rows[1 if fault=='invented-outside-hit' else 0]);n=row['native']
            if fault=='missing-notice':n['group_notices'].pop()
            elif fault=='duplicate-target':n['groups'][0]['targets']*=2
            elif fault=='wrong-child':n['group_children'][0]['name']='invented-child'
            else:n['group_notices']=copy.deepcopy(self.rows[0]['native']['group_notices'][:1])
            with self.subTest(fault=fault),self.assertRaises(AssertionError):self.check(row)


if __name__=='__main__':unittest.main()
