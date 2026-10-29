"""Composition preserves source definitions and cannot author native trajectories."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_moving_overlap_cases import fixtures,prepare_case
from portable_moving_typed_wire import compile_battle


class MovingOverlapInputsTests(unittest.TestCase):
    def test_sealed_shared_operator_scope_is_bound_to_complete_golden_and_independent_audit(self):
        import hashlib,json
        from portable_readiness_semantics import current_movement_overlap_validation,reference_readiness
        from portable_model_gap_audit import verify
        scope=current_movement_overlap_validation();path=ROOT/scope['evidence']
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),scope['evidence_sha256'])
        proof=json.loads(path.read_text());golden=json.loads((ROOT/'research/portable-moving-overlap-v1-expected.json').read_text())
        for k in ('input_sha256','output_sha256','source_sha256','generated_normalized'):self.assertEqual(proof[k],golden[k])
        self.assertEqual(len(golden['entries']),14);self.assertEqual(proof['original_definitions_per_roster'],72)
        audit=proof['independent'];self.assertTrue(audit['calculation_verified']);self.assertEqual(audit['native_cases'],2)
        self.assertEqual([i for g in audit['groups'] for i in g['case_indices']],list(range(14)))
        self.assertFalse(audit['live_parent_receipt_present']);self.assertEqual(audit['gpu_calls'],0)
        model=verify(ROOT)
        for stat in ('enemy_movement_disable','force_move'):
            self.assertEqual(model['missing_stats'][stat]['current_overlap_validation'],scope)
            row=reference_readiness(dict(phase='effect',kind='buff',stat=stat,target='enemies_in_range'))
            self.assertEqual(row['movement_prerequisites']['current_overlap_validation'],scope)
            self.assertFalse(row['gpu_supported']);self.assertEqual(row['lane'],'reference_model_gap')
        for k in ('cuda_verified','default_producer_installed','in_game_motion_policy_verified','in_game_precedence_verified','full_character_verified'):self.assertFalse(scope[k])

    def test_original_operators_and_group_child_survive_both_precedence_inputs(self):
        from calculator.boss_pattern import BossScript
        from enemy_movement_model import EnemyMovement
        snapshots=[]
        for raw in fixtures():
            before=copy.deepcopy(raw);case,p=prepare_case(raw);prepared=copy.deepcopy(p)
            with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No authored hit schedule')),patch.object(EnemyMovement,'advance',side_effect=AssertionError('No authored trajectory')):
                words,meta,_,_=compile_battle(p,case)
            self.assertEqual(raw,before);self.assertEqual(p,prepared)
            self.assertEqual(len(words),123188)
            source=case['original_run']['prepared']['effects']
            self.assertEqual(case['effects'],[r['effect'] for r in source])
            self.assertEqual([case['names'][i] for i in case['owners']],[r['owner'] for r in source])
            self.assertEqual(len(meta['binding_source_indices']),len(source))
            self.assertTrue({'유니','얀','니힐리스타'}<=set(case['names']))
            self.assertTrue({'enemy_movement_disable','force_move'}<={r['effect'].get('stat') for r in source})
            self.assertTrue(any('multi_hit:2' in r['effect'].get('trigger',{}).get('timing',[]) for r in source))
            snapshots.append(p)
        self.assertEqual(snapshots[0]['effects'],snapshots[1]['effects'])
        self.assertEqual(snapshots[0]['chars'],snapshots[1]['chars'])


if __name__=='__main__':unittest.main()
