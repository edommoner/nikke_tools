"""Pre-device wire/source boundaries for the complete shared healing entry."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_enemy_healing_source_contract import project_sources
from portable_enemy_healing_wire import INPUT_WORDS,OUTPUT,check_schema


class EnemyHealingRuntime(unittest.TestCase):
    def test_exact_historical_inverse_and_all_added_dependencies(self):
        ledger=json.loads((ROOT/'tests/fixtures/portable-enemy-healing-source-delta.json').read_text())
        projected=project_sources(ROOT)
        for name,row in ledger['files'].items():
            self.assertEqual(projected[name],row['before'])
        for name in [*ledger['files'],*ledger['added_sources']]:
            with self.subTest(source=name),self.assertRaises(ValueError):
                project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})

    def test_existing_source_contracts_compose_without_normalizer_changes(self):
        from portable_logical_geometry_source_contract import project_sources as logical
        from portable_original_health_parts_source_contract import project_sources as original
        self.assertIn('gpu/world_coordinate_area_entry.slang',logical(ROOT))
        self.assertIn('app/portable_backend.py',original(ROOT))

    def test_only_explicit_entry_accepts_the_new_stride(self):
        from portable_backend import validate_composed_stride
        check_schema(ROOT)
        validate_composed_stride('gpu/world_enemy_healing_entry.slang',INPUT_WORDS,OUTPUT['OUTPUT_WORDS'])
        for source,input_words,output_words in [
            ('gpu/world_enemy_healing_entry.slang',115680,2032000),
            ('gpu/world_coordinate_logical_actor_entry.slang',INPUT_WORDS,2032000),
            ('gpu/world_enemy_healing_entry.slang',INPUT_WORDS,1769856)]:
            with self.subTest(source=source),self.assertRaises(ValueError):
                validate_composed_stride(source,input_words,output_words)

    def test_healing_output_owns_no_prior_scratch_or_history(self):
        from portable_logical_geometry_wire import SCRATCH
        self.assertEqual(OUTPUT['OUTPUT_BASE'],SCRATCH['HEAD_BASE']+SCRATCH['HEAD_WORDS'])
        end=OUTPUT['OUTPUT_BASE']+OUTPUT['RECEIPT_BASE']+OUTPUT['RECEIPTS']*OUTPUT['RECEIPT_WORDS']
        self.assertLessEqual(end,OUTPUT['OUTPUT_WORDS'])
        self.assertLessEqual(INPUT_WORDS,131072)

    def test_cli_remains_development_only_without_a_golden(self):
        import nikke_gpu
        suite=nikke_gpu.SUITES['enemy-healing']
        self.assertTrue(suite['development_only'])
        self.assertEqual((suite['inputs'],suite['native']),(14,6))
        self.assertTrue(nikke_gpu.registered_entry_wire_preflight(suite)['passed'])
        self.assertIn(nikke_gpu.SUITES['logical-actor-geometry']['golden'],suite['support_files'])
        spec=importlib.util.spec_from_file_location('enemy_healing_adapter_test',ROOT/suite['script'])
        adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        rows,raw=adapter.prepare()
        self.assertEqual(len(rows),14)
        self.assertEqual(len(raw),4+14*INPUT_WORDS*4)
        self.assertEqual(sum(domain is not None for _,_,domain in rows),6)
        self.assertEqual(len(rows[0][2][0]['effects']),69)
        self.assertTrue(all(domain[0]['sampled_groups'] for _,_,domain in rows if domain is not None))


if __name__=='__main__':
    unittest.main()
