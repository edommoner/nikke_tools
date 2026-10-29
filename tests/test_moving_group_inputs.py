"""Literal scene composition retains complete source effects and real weapons."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_moving_group_cases import fixtures,prepare_case
from portable_moving_typed_wire import compile_battle

class MovingGroupInputsTests(unittest.TestCase):
    def test_all_original_rows_owners_and_weapons_survive_composed_packing(self):
        from calculator.boss_pattern import BossScript
        from enemy_movement_model import EnemyMovement
        for raw in fixtures():
            before=copy.deepcopy(raw);case,p=prepare_case(raw);original=copy.deepcopy(p)
            with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No authored hit schedule')),patch.object(EnemyMovement,'advance',side_effect=AssertionError('No authored trajectory')):
                words,meta,_,_=compile_battle(p,case)
            self.assertEqual(raw,before);self.assertEqual(p,original)
            self.assertEqual(len(words),123188);self.assertEqual(len(p['effects']),71)
            self.assertEqual(len(meta['binding_source_indices']),71)
            self.assertIn('유니',case['names']);self.assertIn('니힐리스타',case['names'])
            source=case['original_run']['prepared']
            self.assertEqual(case['effects'],[r['effect'] for r in source['effects']])
            self.assertEqual([case['names'][i] for i in case['owners']],[r['owner'] for r in source['effects']])
            self.assertTrue(any(r['effect'].get('stat')=='enemy_movement_disable' for r in p['effects']))
            self.assertTrue(any('multi_hit:2' in r['effect'].get('trigger',{}).get('timing',[]) for r in p['effects']))

    def test_outside_control_changes_declared_scene_without_removing_effects(self):
        rows=fixtures();inside,ip=prepare_case(rows[0]);outside,op=prepare_case(rows[1])
        self.assertEqual(ip['effects'],op['effects']);self.assertEqual(ip['chars'],op['chars'])
        self.assertEqual(inside['duration'],30);self.assertEqual(outside['duration'],30)
        self.assertEqual(inside['enemy_movement'],outside['enemy_movement'])
        self.assertTrue(all(g['shape']['x']==10000. for g in outside['logical_geometry']))
        self.assertNotEqual(rows[0]['patterns'],rows[2]['patterns'])

if __name__=='__main__':unittest.main()
