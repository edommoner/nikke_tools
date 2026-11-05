"""Composition preserves source definitions and cannot author native trajectories."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_moving_overlap_cases import fixtures,prepare_case
from portable_moving_typed_wire import compile_battle


class MovingOverlapInputsTests(unittest.TestCase):
    pass

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
