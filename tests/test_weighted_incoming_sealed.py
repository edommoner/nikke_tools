"""Keep standalone numeric evidence distinct from original Bay battle support."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_backend import source_hashes
from portable_readiness_semantics import reference_readiness
import nikke_gpu as cli
spec=importlib.util.spec_from_file_location('weighted_sealed',ROOT/'research/verify-weighted-incoming.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class WeightedIncomingSealed(unittest.TestCase):
    def test_actual_input_and_common_source_match_full_sealed_output(self):
        config=cli.SUITES['weighted-incoming'];golden=json.loads((ROOT/config['golden']).read_text())
        rows,data=adapter.prepare();self.assertEqual(len(rows),1192);self.assertEqual(len(golden['entries']),1192)
        self.assertEqual(golden['input_sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(golden['source_sha256'],source_hashes(adapter.SOURCE))
        proof=json.loads((ROOT/'tests/fixtures/weighted-incoming-metal-v1.json').read_text());audit=json.loads((ROOT/'tests/fixtures/weighted-incoming-independent-v1.json').read_text())
        for key in ('input_sha256','output_sha256'):
            self.assertEqual(golden[key],proof[key]);self.assertEqual(golden[key],audit[key])
        self.assertTrue(proof['gpu_execution_verified']);self.assertEqual(proof['transport']['device'],'Apple M5')
        self.assertEqual((audit['input_count'],audit['native_cases'],audit['gpu_calls']),(1192,1179,0))
        self.assertFalse(audit['live_parent_receipt_present']);self.assertEqual(audit['original_receipt_sha256'],proof['independent_receipt_sha256'])

    def test_cached_route_is_same_standalone_math_and_cannot_imply_cuda_success(self):
        config=cli.SUITES['weighted-incoming'];cached=cli.SUITES['weighted-incoming-cache-only']
        self.assertFalse(config['development_only']);self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        self.assertFalse(cached.get('require_paired_generation',False))
        for key in ('source','script','golden','inputs','native','input_words','output_words'):self.assertEqual(config[key],cached[key])
        proof=json.loads((ROOT/'tests/fixtures/weighted-incoming-metal-v1.json').read_text())
        for key in ('actual_cuda_verified','carrier_lifecycle_connected','incoming_battle_connected','in_game_rules_verified','public_gpu_admission','full_goal_complete'):self.assertFalse(proof[key])

    def test_original_targets_keep_reference_gap_and_admission_closed(self):
        for target in ('all_allies','self_cover'):
            result=reference_readiness(dict(phase='effect',kind='buff',stat='received_dmg_split',target=target))
            self.assertEqual(result['lane'],'reference_model_gap');self.assertFalse(result['gpu_supported'])
            numeric=result['declared_weighted_allocation_numeric']
            self.assertEqual(numeric['evidence_sha256'],hashlib.sha256((ROOT/numeric['evidence']).read_bytes()).hexdigest())
            self.assertTrue(numeric['metal_verified']);self.assertTrue(numeric['explicit_weights'])
            for key in ('cuda_verified','carrier_lifecycle_connected','incoming_battle_connected','in_game_rules_verified'):self.assertFalse(numeric[key])

if __name__=='__main__':unittest.main()
