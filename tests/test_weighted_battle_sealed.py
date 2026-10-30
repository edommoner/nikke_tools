"""Bind the declared Bay battle route to actual Metal and a fresh CPU audit."""
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app', 'research', 'scripts')]


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


class WeightedBattleSealed(unittest.TestCase):
    def test_current_source_inputs_and_full_output_have_independent_evidence(self):
        import nikke_gpu as cli
        from portable_backend import source_hashes
        config = cli.SUITES['weighted-battle']
        spec = importlib.util.spec_from_file_location('weighted_battle_sealed_adapter', ROOT / config['script'])
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        rows, data = adapter.prepare()
        golden = read(config['golden'])
        proof = read('tests/fixtures/weighted-battle-metal-v1.json')
        audit = read('tests/fixtures/weighted-battle-independent-v1.json')
        self.assertEqual((len(rows), sum(domain is not None for _, _, domain in rows)), (21, 8))
        self.assertEqual(hashlib.sha256(data).hexdigest(), golden['input_sha256'])
        self.assertEqual(source_hashes(adapter.SOURCE), golden['source_sha256'])
        for key in ('input_sha256', 'output_sha256'):
            self.assertEqual(proof[key], golden[key])
            self.assertEqual(audit[key], golden[key])
        self.assertEqual(proof['source_sha256'], golden['source_sha256'])
        self.assertEqual(proof['generated_normalized'], golden['generated_normalized'])
        self.assertTrue(proof['metal_verified'])
        self.assertTrue(audit['calculation_verified'])
        self.assertEqual(audit['gpu_calls'], 0)
        self.assertEqual((audit['input_count'], audit['native_cases']), (21, 8))
        self.assertEqual(proof['runtime_stride_bytes'], 138992)
        self.assertEqual(proof['original_positive_conditional_heals'], 2)

    def test_cached_route_and_source_certificate_do_not_claim_cuda_execution(self):
        import nikke_gpu as cli
        from portable_compiler_certificate import certificate
        config = cli.SUITES['weighted-battle']
        cached = cli.SUITES['weighted-battle-cache-only']
        self.assertFalse(config['development_only'])
        for key in ('source', 'script', 'golden', 'inputs', 'native', 'input_words', 'output_words'):
            self.assertEqual(config[key], cached[key])
        self.assertEqual(cached['cuda_cache_profile'], 'compile-cache-only-v1')
        self.assertTrue(cached['require_paired_generation'])
        raw = (ROOT / config['golden']).read_bytes()
        self.assertEqual(read('research/portable-compiler-full--weighted-battle-source-certificate.json'), certificate('weighted-battle', json.loads(raw), raw))
        proof = read('tests/fixtures/weighted-battle-metal-v1.json')
        for key in ('cuda_verified', 'in_game_rules_verified', 'canonical_default_changed', 'full_goal_complete'):
            self.assertFalse(proof[key])


if __name__ == '__main__':
    unittest.main()
