"""Complete ADD payload ownership and exact inverse of guarded shared hooks."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator.boss_pattern import BossScript
from portable_add_attack_battle_cases import fixtures
from portable_add_attack_battle_wire import LAYOUT,compile_battle,check_schema
from portable_coordinate_original_cases import prepare_case
from portable_add_attack_battle_source_contract import project_sources


class AddAttackBattleTests(unittest.TestCase):
    def test_literal_payload_preserves_original_roster_and_never_runs_a_battle(self):
        for row in fixtures():
            case,prepared=prepare_case(row);before=copy.deepcopy(prepared)
            with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU shot schedule in GPU input')):
                words,meta,bindings,scene=compile_battle(prepared,row['logical_geometry'])
            self.assertEqual(before,prepared);self.assertEqual(len(prepared['effects']),70)
            self.assertEqual(len(words),LAYOUT['INPUT_WORDS'])
            self.assertEqual(words[LAYOUT['BASE']:LAYOUT['BASE']+4],[0x41444231,1,len(row['patterns']),len(bindings)])
            self.assertFalse(meta['add_attack_battle']['CPU_schedule_as_input'])

    def test_exact_shared_source_inverse_and_tamper_rejection(self):
        ledger=json.loads((ROOT/'tests/fixtures/portable-add-attack-battle-source-delta.json').read_text())
        old=project_sources(ROOT)
        for name,r in ledger['files'].items():self.assertEqual(old[name],r['before'])
        for name in [*ledger['files'],*ledger['added_sources']]:
            with self.subTest(path=name),self.assertRaises(ValueError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})

    def test_new_wire_is_disjoint_and_only_its_entry_accepts_it(self):
        from portable_backend import validate_composed_stride
        from portable_logical_geometry_wire import SCRATCH
        check_schema(ROOT)
        self.assertEqual(LAYOUT['OUTPUT_BASE'],SCRATCH['HEAD_BASE']+SCRATCH['HEAD_WORDS'])
        self.assertLessEqual(LAYOUT['OUTPUT_BASE']+LAYOUT['MAP_BASE']+LAYOUT['MAP_ROWS']*2,LAYOUT['OUTPUT_WORDS'])
        validate_composed_stride('gpu/world_add_attack_battle_entry.slang',116464,2032000)
        with self.assertRaises(ValueError):validate_composed_stride('gpu/world_add_attack_battle_entry.slang',115680,2032000)
        with self.assertRaises(ValueError):validate_composed_stride('gpu/world_coordinate_logical_actor_entry.slang',116464,2032000)

    def test_default_actor_and_graph_admission_remain_closed(self):
        from portable_world_schedule_specs import compile_schedule
        from portable_actor_specs import compile_registry
        from calculator.boss_pattern import validate
        row=fixtures()[0]
        with self.assertRaisesRegex(ValueError,'Summon attack lifecycle'):compile_schedule(dict(patterns=row['patterns'],duration=6))
        with self.assertRaisesRegex(ValueError,'source attacks'):compile_registry(validate(row['patterns']),pools=True)

    def test_full_actor_slot_and_generation_are_read_not_serialized(self):
        runtime=(ROOT/'gpu/world_add_attack_battle_runtime.slang').read_text()
        self.assertIn('nextWorldAddAttack(cursor,results[p],results[p+1]!=0,actorNumber(p+8)',runtime)
        self.assertIn('addAttackEmit(s,w,node,slot,results[p],index,when)',runtime)
        self.assertIn('collectWorldEnemyAttackFlat(s,0,when)',runtime)

    def test_registered_proof_and_cached_profile_keep_ammo_and_cuda_unverified(self):
        from portable_readiness_semantics import enemy_ammo_prerequisites
        p=enemy_ammo_prerequisites();r=p['declared_add_battle_validation'];raw=(ROOT/r['evidence']).read_bytes();a=json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),r['evidence_sha256'])
        self.assertEqual((a['input_count'],a['native_cases']),(17,6));self.assertTrue(a['calculation_verified'])
        self.assertEqual(a['gpu_calls'],0);self.assertFalse(r['ammo_connected']);self.assertFalse(r['cuda_verified'])
        self.assertFalse(p['enemy_shot_reload_connected'])
        sys.path.insert(0,str(ROOT/'scripts'));import nikke_gpu
        normal=nikke_gpu.SUITES['add-attack-battle'];cached=nikke_gpu.SUITES['add-attack-battle-cache-only']
        for key in ('script','source','golden','inputs','native','input_words','output_words'):self.assertEqual(normal[key],cached[key])
        self.assertTrue(cached['require_paired_generation']);self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        from portable_backend import source_hashes
        current_raw=(ROOT/normal['golden']).read_bytes();current=json.loads(current_raw)
        old=json.loads((ROOT/'research/portable-add-attack-battle-v1-expected.json').read_text())
        self.assertEqual(current['source_sha256'],source_hashes(normal['source']))
        self.assertEqual(current['entries'],old['entries']);self.assertEqual(current['output_sha256'],old['output_sha256'])
        cert=json.loads((ROOT/nikke_gpu.SUITES['compiler-full--add-attack-battle']['golden']).read_text())
        self.assertEqual(cert['baseline_golden_sha256'],hashlib.sha256(current_raw).hexdigest())
        self.assertEqual(cert['source_sha256'],current['source_sha256'])


if __name__=='__main__':unittest.main()
