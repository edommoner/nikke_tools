"""Complete disjoint banks and original definitions; packing does not simulate."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from portable_moving_typed_cases import fixtures,prepare
from portable_moving_typed_wire import compile_battle,check_schema,output_regions,INPUT,OUTPUT,LOGICAL_BASE,MOVEMENT_BASE,AIM_BASE
from portable_specs import LIMITS as L,FIELDS as F

class MovingTypedWireTests(unittest.TestCase):
    def test_full_rosters_pack_literal_motion_without_any_native_clock_or_position(self):
        from calculator.boss_pattern import BossScript
        from enemy_movement_model import EnemyMovement
        check_schema(ROOT)
        for row in fixtures():
            c,p=prepare(row);before=copy.deepcopy(p)
            with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No packed clock')),patch.object(EnemyMovement,'advance',side_effect=AssertionError('No packed trajectory')):
                words,meta,actors,_=compile_battle(p,c)
            self.assertEqual(p,before);self.assertEqual(len(words),INPUT);self.assertEqual(len(p['effects']),len(meta['binding_source_indices']))
            self.assertEqual(words[MOVEMENT_BASE+6],1);self.assertEqual(words[LOGICAL_BASE:LOGICAL_BASE+2],[0x4c414731,1])
            for tag in meta['enemy_movement']['domains']:
                at=L['DEFINITION_BASE']+tag['row']*L['DEFINITION_WORDS']
                self.assertEqual((words[at+F['KIND']],words[at+F['STAT']]),(0,0))
            self.assertFalse(meta['moving_typed_geometry']['precomputed_positions']);self.assertFalse(meta['moving_typed_geometry']['gpu_admitted'])
    def test_all_existing_history_capacities_and_scratch_owners_fit_without_overlap(self):
        rows=output_regions();cursor=0
        for row in rows:self.assertEqual(row.base,cursor);cursor=row.end
        self.assertEqual(cursor,OUTPUT);self.assertEqual(AIM_BASE+512,OUTPUT)
        self.assertEqual(next(r.words for r in rows if r.name=='shared-complete-skill-history'),1920*48)
        self.assertEqual(next(r.words for r in rows if r.name=='movement-frames'),4096*16)
        self.assertEqual(next(r.words for r in rows if r.name=='movement-segments'),4096*16)
    def test_foreign_owner_missing_attachment_and_legacy_stride_are_rejected(self):
        from portable_backend import validate_composed_stride
        validate_composed_stride('gpu/world_moving_typed_entry.slang',INPUT,OUTPUT)
        for input_words,output_words in ((117476,OUTPUT),(INPUT,2032000)):
            with self.assertRaises(ValueError):validate_composed_stride('gpu/world_moving_typed_entry.slang',input_words,output_words)
        for variant in ('owner','missing','unknown'):
            c,p=prepare(fixtures()[0])
            if variant=='owner':c['typed_bindings'][0]['owner']=[5,2,1]
            if variant=='missing':c['typed_attachment']['bindings'][0]['typed_label']='fixed-typed'
            if variant=='unknown':c['typed_attachment']['bindings'][0]['typed_label']='unknown'
            with self.subTest(variant=variant),self.assertRaises(ValueError):compile_battle(p,c)

if __name__=='__main__':unittest.main()
