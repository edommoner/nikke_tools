"""Fresh fixed-source proofs and compiler identities stay scoped to their suites."""
import hashlib
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','scripts')]
import nikke_gpu


class DeliveryRecertification(unittest.TestCase):
    def test_fresh_receipts_cover_every_original_input_once(self):
        from portable_readiness_semantics import reference_readiness
        r=reference_readiness(dict(phase='effect',category='trigger',operator=dict(domain='timing',descriptor='multi_hit:2')))
        proof=r['shared_delivery_recertification'];counts=[]
        for row in proof['evidence']:
            raw=(ROOT/row['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
            d=json.loads(raw);self.assertTrue(d['calculation_verified']);self.assertEqual(d['gpu_calls'],0)
            self.assertFalse(d['live_parent_receipt_present'])
            self.assertEqual([i for g in d['groups'] for i in g['case_indices']],list(range(d['input_count'])))
            counts.append((d['input_count'],d['native_cases']))
        self.assertEqual(counts,[(13,6),(5,5)])
        self.assertFalse(proof['includes_post_death_shot_regression'])
        self.assertFalse(proof['current_cuda_verified']);self.assertFalse(r['gpu_supported'])
        self.assertEqual(r['lane'],'reference_model_gap')

    def test_registered_goldens_match_current_source_and_exact_certificates(self):
        from portable_backend import source_hashes
        for suite in ('logical-actor-geometry','logical-actor-rosters'):
            config=nikke_gpu.SUITES[suite];raw=(ROOT/config['golden']).read_bytes();g=json.loads(raw)
            self.assertTrue(config['golden'].endswith('-v2-expected.json'))
            self.assertEqual(g['source_sha256'],source_hashes(config['source']))
            compiler=nikke_gpu.SUITES['compiler-full--'+suite]
            c=json.loads((ROOT/compiler['golden']).read_text())
            self.assertEqual(c['baseline_suite'],suite)
            self.assertEqual(c['baseline_golden_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(c['source_sha256'],g['source_sha256'])
            self.assertEqual(c['generated_normalized'],g['generated_normalized'])
            self.assertFalse(c['calculation_verified']);self.assertFalse(c['executable_battle_verified'])

    def test_historical_goldens_and_certificates_remain_available(self):
        for suite in ('logical-actor-geometry','logical-actor-rosters'):
            raw=(ROOT/'research'/('portable-'+suite+'-v1-expected.json')).read_bytes()
            c=json.loads((ROOT/'research'/('portable-compiler-full--'+suite+'-v1-source-certificate.json')).read_text())
            self.assertEqual(c['baseline_golden_sha256'],hashlib.sha256(raw).hexdigest())

    def test_shared_test_baseline_follows_registered_golden(self):
        path=nikke_gpu.SUITES['logical-actor-geometry']['golden']
        for suite in ('enemy-healing','logical-actor-rosters','logical-actor-rosters-cache-only'):
            self.assertIn(path,nikke_gpu.SUITES[suite]['support_files'])


if __name__=='__main__':unittest.main()
