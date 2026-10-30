"""Bind the full battle seal, independent audit and scoped classification."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_backend import source_hashes

def read(name):return json.loads((ROOT/name).read_text())
class CoverSealed(unittest.TestCase):
    def test_same_full_inputs_native_and_explicitly_scoped_shared_source(self):
        s=importlib.util.spec_from_file_location('sealed_cover_adapter',ROOT/'research/verify-cover-defense-battle.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        rows,data=m.prepare();golden=read('research/portable-cover-defense-battle-v1-expected.json')
        self.assertEqual(len(rows),11);self.assertEqual(sum(d is not None for _,_,d in rows),4)
        self.assertEqual(hashlib.sha256(data).hexdigest(),golden['input_sha256'])
        self.assertEqual([r[0] for r in rows],[r['name'] for r in golden['entries']])
        from portable_received_sum_source_contract import historical_hashes
        self.assertEqual(historical_hashes(ROOT,m.SOURCE),golden['source_sha256'])
        proof=read('tests/fixtures/cover-defense-battle-metal-v1.json');audit=read('tests/fixtures/cover-defense-battle-independent-v1.json')
        self.assertTrue(proof['metal_verified']);self.assertTrue(proof['independently_audited'])
        for key in ('input_sha256','output_sha256'):
            self.assertEqual(proof[key],golden[key]);self.assertEqual(audit[key],golden[key])
        self.assertEqual(proof['source_sha256'],golden['source_sha256'])
        self.assertEqual(proof['generated_normalized'],golden['generated_normalized'])
        self.assertFalse(audit['live_parent_receipt_present']);self.assertEqual(audit['gpu_calls'],0)
        self.assertEqual((audit['input_count'],audit['native_cases']),(11,4))
    def test_source_certificate_is_same_audited_source_and_not_cuda_execution(self):
        from portable_compiler_certificate import certificate
        import nikke_gpu
        raw=(ROOT/'research/portable-cover-defense-battle-v1-expected.json').read_bytes();golden=json.loads(raw)
        cert=read('research/portable-compiler-full--cover-defense-battle-source-certificate.json')
        self.assertEqual(cert,certificate('cover-defense-battle',golden,raw))
        self.assertTrue(nikke_gpu.full_compiler(dict(suite='compiler-full--cover-defense-battle')))
        self.assertFalse(cert['calculation_verified']);self.assertFalse(cert['executable_battle_verified'])
    def test_default_gap_stays_closed_with_scoped_modifier_evidence(self):
        from portable_readiness_semantics import reference_readiness
        result=reference_readiness(dict(phase='effect',kind='buff',stat='cover_def_pct',target='allies_top_atk:3'))
        self.assertEqual(result['lane'],'reference_model_gap');self.assertFalse(result['gpu_supported'])
        proof=result['declared_cover_defense_battle_gpu'];self.assertTrue(proof['metal_verified'])
        self.assertEqual(proof['evidence_sha256'],hashlib.sha256((ROOT/proof['evidence']).read_bytes()).hexdigest())
        for key in ('cuda_verified','canonical_default_changed','in_game_rules_verified'):self.assertFalse(proof[key])
        self.assertTrue(proof['nonzero_received_gpu_verified']);self.assertTrue(proof['varied_coefficient_gpu_verified'])
        saved=read(proof['evidence']);self.assertFalse(saved['full_character_verified']);self.assertFalse(saved['full_goal_complete'])
        self.assertEqual(saved['received_snapshot_values'],[-8.,0.]);self.assertEqual(saved['incoming_coefficient_values'],[33.33,100.,137.5,250.])
        self.assertEqual(saved['same_claim_retries'],0)

if __name__=='__main__':unittest.main()
