"""Sealed calculation, independent provenance and conservative work routing."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]

class NamedRangeBattleCli(unittest.TestCase):
    def test_cached_profile_keeps_calculation_and_requires_paired_generation(self):
        import nikke_gpu as cli
        a=cli.SUITES['named-range-battle'];b=cli.SUITES['named-range-battle-cache-only']
        for key in ('script','source','golden','inputs','native','input_words','output_words','development_only'):
            self.assertEqual(a[key],b[key])
        self.assertFalse(a['development_only']);self.assertTrue(b['require_paired_generation'])
        self.assertEqual(b['cuda_cache_profile'],'compile-cache-only-v1')
        self.assertIn('research/portable-compiler-full--named-range-battle-source-certificate.json',a['support_files'])
    def test_independent_groups_and_source_certificate_anchor_exact_golden(self):
        from portable_named_range_battle_evidence import validation
        v=validation();raw=(ROOT/v['evidence']).read_bytes();r=json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),v['evidence_sha256'])
        self.assertTrue(r['calculation_verified']);self.assertEqual(r['gpu_calls'],0)
        self.assertFalse(r['live_parent_receipt_present']);self.assertEqual((r['input_count'],r['native_cases']),(16,4))
        self.assertEqual([i for g in r['groups'] for i in g['case_indices']],list(range(16)))
        self.assertTrue(all(g['elapsed_seconds']<=r['per_group_timeout_seconds'] for g in r['groups']))
        raw=(ROOT/'research/portable-named-range-battle-v1-expected.json').read_bytes();golden=json.loads(raw)
        cert=json.loads((ROOT/'research/portable-compiler-full--named-range-battle-source-certificate.json').read_text())
        self.assertEqual(cert['baseline_golden_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(cert['source_sha256'],golden['source_sha256'])
        self.assertEqual(cert['generated_normalized'],golden['generated_normalized'])
        self.assertEqual(r['output_sha256'],golden['output_sha256']);self.assertEqual(r['input_sha256'],golden['input_sha256'])
        self.assertFalse(cert['executable_battle_verified']) # Source provenance alone is not CUDA execution.
    def test_model_audit_and_routing_share_proof_without_opening_default(self):
        from portable_named_range_battle_evidence import validation
        from portable_readiness_semantics import reference_readiness
        from portable_model_gap_audit import verify
        report=verify(ROOT)
        for stat in ('effect_range_pct','effect_target_count_add'):
            issue=dict(phase='effect',kind='buff',stat=stat,target='self')
            routed=reference_readiness(issue)
            self.assertEqual(routed['declared_named_range_battle_metal_validation'],validation())
            self.assertEqual(report['missing_stats'][stat]['declared_named_range_battle_metal_validation'],validation())
            self.assertFalse(routed['gpu_supported']);self.assertFalse(routed['full_character_verified'])
        for flag in ('current_cuda_verified','default_producer_installed','in_game_radius_semantics_verified','spatial_nearest_order_verified'):
            self.assertFalse(validation()[flag])

if __name__=='__main__':unittest.main()
