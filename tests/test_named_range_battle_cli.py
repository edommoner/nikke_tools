"""Sealed calculation, independent provenance and conservative work routing."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]

class NamedRangeBattleCli(unittest.TestCase):
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

if __name__=='__main__':unittest.main()
