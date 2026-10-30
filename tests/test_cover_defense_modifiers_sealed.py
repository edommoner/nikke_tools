"""Current compensated aggregate, original Noah source and old raw retention."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
def read(path):return json.loads((ROOT/path).read_text())
class ModifiersSealed(unittest.TestCase):
    def test_historical_source_and_all_thirteen_inputs_remain_bound_to_fresh_seal(self):
        from portable_weighted_incoming_source_contract import historical_hashes
        s=importlib.util.spec_from_file_location('modifier_sealed_adapter',ROOT/'research/verify-cover-defense-modifiers.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows,data=m.prepare()
        golden=read('research/portable-cover-defense-modifiers-v1-expected.json');proof=read('tests/fixtures/cover-defense-modifiers-metal-v1.json');audit=read('tests/fixtures/cover-defense-modifiers-independent-v1.json')
        self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(13,6))
        self.assertEqual(hashlib.sha256(data).hexdigest(),golden['input_sha256']);self.assertEqual(historical_hashes(ROOT,m.SOURCE),golden['source_sha256'])
        for key in ('input_sha256','output_sha256'):
            self.assertEqual(proof[key],golden[key]);self.assertEqual(audit[key],golden[key])
        self.assertEqual(proof['source_sha256'],golden['source_sha256']);self.assertEqual(proof['generated_normalized'],golden['generated_normalized'])
        self.assertFalse(audit['live_parent_receipt_present']);self.assertEqual(audit['gpu_calls'],0);self.assertEqual((audit['input_count'],audit['native_cases']),(13,6))
        self.assertTrue(proof['compensated_received_aggregate']);self.assertEqual(proof['runtime_extra_bytes'],40)
        self.assertEqual(proof['original_probability_activations'],[3,3]);self.assertEqual(proof['nonzero_received_receipts'],22)
    def test_prior_all_bytes_and_source_only_certificate_keep_scopes_separate(self):
        from portable_compiler_certificate import certificate
        r=read('tests/fixtures/cover-defense-modifiers-retention-v1.json');golden=read('research/portable-cover-defense-modifiers-v1-expected.json');old=read('research/portable-cover-defense-battle-v1-expected.json')
        self.assertTrue(r['all_reference_cases_retained']);self.assertEqual((r['retained_cases'],r['candidate_cases']),(11,13));self.assertEqual(r['retained_output_bytes'],90152128)
        self.assertEqual(r['reference_readback_sha256'],old['output_sha256']);self.assertEqual(r['candidate_readback_sha256'],golden['output_sha256'])
        self.assertEqual(r['changed'],[]);self.assertFalse(r['calculation_verified']);self.assertEqual(r['gpu_calls'],0)
        raw=(ROOT/'research/portable-cover-defense-modifiers-v1-expected.json').read_bytes()
        cert=read('research/portable-compiler-full--cover-defense-modifiers-source-certificate.json');self.assertEqual(cert,certificate('cover-defense-modifiers',golden,raw))
    def test_current_classification_and_main_cli_share_the_complete_joined_cohort(self):
        import nikke_gpu
        from portable_readiness_semantics import reference_readiness
        a=nikke_gpu.SUITES['cover-defense-battle'];b=nikke_gpu.SUITES['cover-defense-modifiers']
        for key in ('script','source','golden','inputs','native','input_words','output_words'):self.assertEqual(a[key],b[key])
        self.assertFalse(a['development_only']);self.assertEqual((a['inputs'],a['native']),(13,6))
        result=reference_readiness(dict(phase='effect',kind='buff',stat='cover_def_pct',target='allies_top_atk:3'));p=result['declared_cover_defense_battle_gpu']
        self.assertFalse(result['gpu_supported']);self.assertFalse(p['current_received_sum_source_recertified']);self.assertTrue(p['historical_received_sum_source_verified']);self.assertTrue(p['nonzero_received_gpu_verified']);self.assertTrue(p['varied_coefficient_gpu_verified'])
        self.assertEqual(p['evidence_sha256'],hashlib.sha256((ROOT/p['evidence']).read_bytes()).hexdigest())
        self.assertFalse(p['cuda_verified']);self.assertFalse(p['canonical_default_changed'])

if __name__=='__main__':unittest.main()
