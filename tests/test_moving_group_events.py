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

    def test_sealed_proof_and_scope_are_bound_to_golden_and_saved_events(self):
        import hashlib
        from portable_readiness_semantics import movement_contract
        scope=movement_contract()['declared_group_composition'];path=ROOT/scope['evidence']
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),scope['evidence_sha256'])
        proof=json.loads(path.read_text());golden=json.loads((ROOT/'research/portable-moving-group-v1-expected.json').read_text())
        for key in ('input_sha256','output_sha256','source_sha256','generated_normalized'):self.assertEqual(proof[key],golden[key])
        self.assertEqual(hashlib.sha256((ROOT/'tests/fixtures/moving-group-native-events-v1.json').read_bytes()).hexdigest(),proof['event_projection_sha256'])
        audit=proof['independent_audit'];self.assertTrue(audit['calculation_verified'])
        self.assertEqual([i for g in audit['groups'] for i in g['case_indices']],list(range(15)))
        self.assertFalse(audit['live_parent_receipt_present']);self.assertEqual(audit['gpu_calls'],0)
        self.assertEqual(proof['gpu_execution_count'],1);self.assertEqual(proof['gpu_retries'],0)
        self.assertTrue(proof['generation_cache']['hit']);self.assertEqual(proof['generation_cache']['compiler_invocations'],0)
        self.assertTrue(proof['transport']['pipeline_cache']['hit'])
        self.assertTrue(proof['movement_omission']['real_group_notices_changed'])
        for key in ('cuda_verified','default_producer_installed','in_game_motion_policy_verified','in_game_attachment_policy_verified','actual_spatial_recipient_selection_verified','full_character_verified','full_goal_complete'):self.assertFalse(proof[key])

if __name__=='__main__':unittest.main()
