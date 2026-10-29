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
    def test_full_frame_and_segment_banks_do_not_reduce_existing_capacities(self):
        from portable_moving_typed_wire import output_regions as old
        from portable_backend import validate_composed_stride
        from portable_wire_layout import check_metal
        check_schema(ROOT);check_metal(ROOT,OUTPUT)
        rows=output_regions();self.assertEqual(rows[:-3],old()[:-3]);cursor=0
        for r in rows:self.assertEqual(r.base,cursor);cursor=r.end
        self.assertEqual(cursor,OUTPUT);self.assertGreaterEqual(CAPACITY,127*1801)
        self.assertEqual(rows[-3].words,262144*16);self.assertEqual(rows[-2].words,262144*16)
        self.assertEqual(AIM_BASE+512,OUTPUT)
        validate_composed_stride('gpu/world_moving_many_entry.slang',INPUT,OUTPUT)
        for shape in [(INPUT,2165136),(INPUT,OUTPUT-1),(INPUT-1,OUTPUT)]:
            with self.assertRaises(ValueError):validate_composed_stride('gpu/world_moving_many_entry.slang',*shape)
    def test_excess_actor_and_unreviewed_source_cannot_be_admitted(self):
        row=fixtures()[0];row['patterns'][0]['spec']['count']=128
        row['body']['enemy']['patterns']=copy.deepcopy(row['patterns'])
        with self.assertRaises(ValueError):case,p=prepare_case(row);compile_battle(p,case)
        from portable_moving_many_source_contract import project_sources
        ledger=json.loads((ROOT/'tests/fixtures/portable-moving-many-source-delta.json').read_text());out=project_sources(ROOT)
        for name,r in ledger['files'].items():
            self.assertEqual(hashlib.sha256(out[name].encode()).hexdigest(),r['before_sha256'])
            with self.subTest(name=name),self.assertRaises(ValueError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})
    def test_old_layouts_remain_byte_exact_with_default_capacity(self):
        from portable_enemy_movement_wire import check_schema as old_motion
        from portable_moving_typed_wire import check_schema as old_physical
        old_motion(ROOT);old_physical(ROOT)

    def test_maximum_slot_proof_keeps_full_history_and_separate_scope(self):
        from portable_readiness_semantics import movement_contract
        scope=movement_contract()['declared_maximum_slots'];p=ROOT/scope['evidence']
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),scope['evidence_sha256'])
        proof=json.loads(p.read_text());golden=json.loads((ROOT/'research/portable-moving-many-v1-expected.json').read_text())
        for key in ('input_sha256','output_sha256','source_sha256','generated_normalized'):self.assertEqual(proof[key],golden[key])
        native=proof['retained_native'];self.assertEqual(native['actor_handles'],127)
        self.assertEqual(native['frames'],127*1801);self.assertEqual(native['segments'],228854)
        self.assertTrue(proof['all_actor_frames_and_segments_compared']);self.assertTrue(proof['all_movement_padding_compared'])
        audit=proof['independent_audit'];self.assertTrue(audit['calculation_verified'])
        self.assertEqual([i for g in audit['groups'] for i in g['case_indices']],list(range(13)))
        self.assertFalse(audit['live_parent_receipt_present']);self.assertEqual(audit['gpu_calls'],0)
        self.assertEqual(proof['gpu_execution_count'],1);self.assertEqual(proof['gpu_retries'],0)
        self.assertEqual(proof['transport']['output_bytes'],13*OUTPUT*4)
        for key in ('cuda_verified','precomputed_positions','default_producer_installed','in_game_motion_policy_verified','in_game_attachment_policy_verified','actual_spatial_recipient_selection_verified','all_simultaneous_hits_verified','full_character_verified','full_goal_complete'):self.assertFalse(proof[key])

if __name__=='__main__':unittest.main()
