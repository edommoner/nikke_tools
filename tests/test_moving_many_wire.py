"""Maximum slot capacity is literal, disjoint and shared across host/device."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_moving_many_cases import fixtures,prepare_case
from portable_moving_many_wire import compile_battle,check_schema,output_regions,INPUT,OUTPUT,CAPACITY,AIM_BASE

class MovingManyWireTests(unittest.TestCase):
    def test_all_127_actors_pack_without_running_a_clock_or_trajectory(self):
        from calculator.boss_pattern import BossScript
        from enemy_movement_model import EnemyMovement
        row=fixtures()[0];before=copy.deepcopy(row);case,p=prepare_case(row);original=copy.deepcopy(p)
        with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No packed clock')),patch.object(EnemyMovement,'advance',side_effect=AssertionError('No packed trajectory')):
            words,meta,actors,_=compile_battle(p,case)
        self.assertEqual(row,before);self.assertEqual(p,original);self.assertEqual(len(words),INPUT)
        self.assertEqual(len(actors),128);self.assertEqual(len(case['enemy_movement']['actors']),127)
        self.assertEqual(len(p['effects']),71);self.assertEqual(case['duration'],30)
        self.assertFalse(meta['moving_typed_geometry']['precomputed_positions'])
    def test_excess_actor_cannot_be_admitted(self):
        row = fixtures()[0]
        row['patterns'][0]['spec']['count'] = 128
        row['body']['enemy']['patterns'] = copy.deepcopy(row['patterns'])
        with self.assertRaises(ValueError):
            (case, p) = prepare_case(row)
            compile_battle(p, case)
    def test_old_layouts_remain_byte_exact_with_default_capacity(self):
        from portable_enemy_movement_wire import check_schema as old_motion
        from portable_moving_typed_wire import check_schema as old_physical
        old_motion(ROOT);old_physical(ROOT)


if __name__=='__main__':unittest.main()
