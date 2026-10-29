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
    def test_shared_source_inverse_is_exact_and_rejects_unreviewed_source_bytes(self):
        import hashlib,json
        from portable_moving_typed_source_contract import project_sources
        ledger=json.loads((ROOT/'tests/fixtures/portable-moving-typed-source-delta.json').read_text());out=project_sources(ROOT)
        for name,row in ledger['files'].items():
            self.assertEqual(hashlib.sha256(out[name].encode()).hexdigest(),row['before_sha256'])
            with self.subTest(file=name),self.assertRaises(ValueError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})
        from portable_enemy_movement_source_contract import project_sources as historical
        self.assertIn('gpu/logical_actor_geometry_runtime.slang',historical(ROOT))
    def test_metal_receipt_and_independent_groups_do_not_admit_cuda_or_game_policy(self):
        import hashlib,json
        from portable_readiness_semantics import movement_contract
        scope=movement_contract()['declared_typed_composition'];raw=(ROOT/scope['evidence']).read_bytes();proof=json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),scope['evidence_sha256'])
        golden=json.loads((ROOT/'research/portable-moving-typed-v1-expected.json').read_text())
        for key in ('input_sha256','output_sha256','source_sha256','generated_normalized'):self.assertEqual(proof[key],golden[key])
        audit=proof['independent_audit'];self.assertTrue(audit['calculation_verified']);self.assertFalse(audit['live_parent_receipt_present'])
        self.assertEqual([i for g in audit['groups'] for i in g['case_indices']],list(range(18)))
        self.assertTrue(all(g['elapsed_seconds']<=180 for g in audit['groups']))
        self.assertEqual(audit['gpu_calls'],0);self.assertEqual(proof['gpu_execution_count'],1);self.assertEqual(proof['gpu_retries'],0)
        self.assertEqual((proof['inputs'],proof['native_cases'],proof['rejected_cases']),(18,6,12))
        self.assertTrue(proof['shared_clock_actor_registry_carriers_and_canonical_pellet'])
        self.assertFalse(proof['typed_shape_query_diagnostics_gpu_serialized'])
        for key in ('cuda_verified','default_producer_installed','in_game_attachment_policy_verified','full_character_verified','full_goal_complete'):self.assertFalse(proof[key])
    def test_old_physical_dependency_guard_checks_exact_projected_bytes(self):
        import hashlib
        import portable_coordinate_typed_aim_source_contract as aims
        import portable_coordinate_typed_weapon_source_contract as physical
        upstream=aims.project_sources(ROOT);ledger=physical.ledger(ROOT);name='gpu/coordinate_typed_weapon_runtime.slang'
        self.assertNotEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),ledger['added_sources'][name])
        self.assertEqual(hashlib.sha256(upstream[name].encode()).hexdigest(),ledger['added_sources'][name])
        with patch.object(aims,'project_sources',return_value=upstream):self.assertIn(name,physical.project_sources(ROOT))
        changed=dict(upstream);changed[name]+='\n'
        with patch.object(aims,'project_sources',return_value=changed),self.assertRaises(AssertionError):physical.project_sources(ROOT)

if __name__=='__main__':unittest.main()
