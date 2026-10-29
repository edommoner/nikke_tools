"""Saved CUDA words use the same full comparator; no GPU execution in tests."""
import hashlib,importlib.util,json,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('cuda_movement_word_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
from portable_readiness_semantics import movement_contract
from portable_native_status import expected

class CudaMovementWordsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope=movement_contract()['declared_math_validation']
        cls.raw=(ROOT/cls.scope['cuda_evidence']).read_bytes();cls.proof=json.loads(cls.raw)
    def test_all_exported_words_match_fresh_native_and_sealed_metal_golden(self):
        p=self.proof
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),self.scope['cuda_evidence_sha256'])
        with cli.forbid_gpu():
            m=dict(suite='enemy-movement-math');adapter=cli.open_suite(m);entries,data=cli.prepare_entries(adapter,m)
            golden=cli.load(ROOT/'research/portable-enemy-movement-math-v1-expected.json');rows=p['readback_words']
            self.assertEqual(len(entries),43);self.assertEqual(len(rows),43);self.assertEqual(cli.sha(data),golden['input_sha256'])
            # Historical word evidence stays tied to its own sealed source;
            # a future GPU-only edit still needs fresh execution and seal.
            self.assertEqual(golden['source_sha256'],p['source_sha256'])
            for i,((name,_,domain),block) in enumerate(zip(entries,rows,strict=True)):
                with self.subTest(case=name):
                    self.assertEqual(len(block),16);self.assertTrue(all(type(w) is int and 0<=w<=0xffffffff for w in block))
                    if domain is None:adapter.validate_rejection(block,name);native=dict(status=64)
                    else:
                        self.assertEqual(block[0],expected(adapter,cli.SUITES[m['suite']],domain));native=adapter.compare(block,domain)
                    actual=dict(name=name,input_sha256=cli.sha(data[4+i*96:4+(i+1)*96]),output_sha256=cli.sha(struct.pack('<16I',*block)),native_sha256=adapter.cross.digest(native))
                    self.assertEqual(actual,golden['entries'][i]);self.assertEqual(actual,p['entries'][i])
            raw=struct.pack('<688I',*(w for row in rows for w in row))
            self.assertEqual(len(raw),2752);self.assertEqual(cli.sha(raw),golden['output_sha256']);self.assertEqual(cli.sha(raw),p['output_sha256'])
    def test_cache_hit_and_outer_service_failure_do_not_become_full_battle_success(self):
        p=self.proof;peer=p['peer_verification'];self.assertTrue(self.scope['cuda_verified'])
        self.assertTrue(p['independent_native_word_comparison_verified']);self.assertTrue(p['all_exported_cuda_and_retained_metal_words_equal'])
        self.assertEqual(p['gpu_calls_during_import_and_audit'],0);self.assertFalse(p['source_host_envelope_independently_audited_on_mac'])
        self.assertEqual(p['status_counts'],{'0':32,'16':2,'64':9})
        self.assertTrue(peer['calculation_verified']);self.assertTrue(peer['cubin_cache_hit'])
        self.assertEqual(peer['compile_nvrtc_compile_calls'],1);self.assertEqual(peer['run_nvrtc_compile_calls'],0)
        self.assertEqual(peer['launch_calls'],1);self.assertEqual(peer['retries'],0)
        for stage in ('compile','run'):
            self.assertEqual(peer[stage+'_outer_exit_code'],2);self.assertEqual(peer[stage+'_inner_exit_code'],0)
            self.assertEqual(peer[stage+'_outer_job_post_members'],0);self.assertTrue(peer[stage+'_outer_process_preserved'])
            self.assertFalse(peer[stage+'_outer_timed_out']);self.assertFalse(peer[stage+'_outer_service_preservation_verified'])
        for key in ('service_preservation_verified','overall_passed','gpu_world_consumer_cuda_verified','full_goal_complete'):self.assertFalse(p[key])
        self.assertFalse(peer['full_battle_verified']);self.assertFalse(peer['all_characters_verified'])
        self.assertFalse(movement_contract()['declared_battle_validation']['cuda_verified'])

if __name__=='__main__':unittest.main()
