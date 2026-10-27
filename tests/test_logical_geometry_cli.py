"""Private development registration, preparation and strict transport gates."""
import importlib.util,sys,unittest
import hashlib,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,nikke_gpu
from calculator import timeline
from portable_backend import validate_composed_stride
from portable_wire_layout import check_metal

def adapter():
    spec=importlib.util.spec_from_file_location('logical_cli_test_adapter',ROOT/'research/verify-logical-actor-geometry.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class LogicalGeometryCLI(unittest.TestCase):
    def test_registered_wire_and_existing_swift_guard_agree_without_devices(self):
        config=nikke_gpu.SUITES['logical-actor-geometry']
        self.assertFalse(config['development_only']);self.assertTrue(config['parent_oracle_reuse'])
        baseline=json.loads((ROOT/config['golden']).read_text())
        self.assertEqual(len(baseline['entries']),13)
        cached=nikke_gpu.SUITES['logical-actor-geometry-cache-only']
        self.assertEqual(cached['golden'],config['golden'])
        self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        self.assertTrue(cached['require_paired_generation'])
        self.assertEqual(config['upstream_documents'],['research/upstream/nikke-calc-master/docs/IMPL-STATUS.md'])
        self.assertTrue((ROOT/config['upstream_documents'][0]).is_file())
        self.assertTrue(nikke_gpu.registered_entry_wire_preflight(config)['passed'])
        self.assertTrue(check_metal(ROOT,2032000)['passed'])
        for source,iw,ow in [(config['source'],109968,2032000),(config['source'],115680,1769856),('gpu/unregistered_logical.slang',115680,2032000)]:
            with self.subTest(source=source,iw=iw,ow=ow),self.assertRaises(ValueError):validate_composed_stride(source,iw,ow)

    def test_thirteen_inputs_retain_six_original_battles_and_raw_negatives(self):
        m=adapter()
        with patch.object(timeline,'simulate',side_effect=AssertionError('No native battle in preparation')):rows,raw=m.prepare()
        self.assertEqual(len(rows),13);self.assertEqual(len(raw),4+13*115680*4)
        self.assertEqual(sum(domain is not None for _,_,domain in rows),6)
        self.assertEqual(len({name for name,_,_ in rows}),13)
        for name,words,domain in rows:
            self.assertEqual(len(words),115680)
            if domain is not None:self.assertEqual(domain[1]['coordinate_original_input']['prepared_definitions'],68)
            else:self.assertTrue(name.startswith('reject/logical-actor-geometry/'))

    def test_failed_readback_cannot_start_native_comparison(self):
        m=adapter()
        with patch.object(m,'native_reference',side_effect=AssertionError('Must stop before native')) as native:
            for block in ([64], [64]+[0]*(2032000-1)):
                with self.assertRaisesRegex(AssertionError,'Complete successful'):m.compare(block,None)
            native.assert_not_called()

    def test_scoped_metal_proof_does_not_open_default_or_cuda_admission(self):
        from portable_readiness_semantics import reference_readiness
        raw=(ROOT/'tests/fixtures/logical-actor-independent-v1.json').read_bytes();audit=json.loads(raw)
        self.assertTrue(audit['calculation_verified']);self.assertEqual(audit['gpu_calls'],0)
        self.assertEqual([i for g in audit['groups'] for i in g['case_indices']],list(range(13)))
        for descriptor in ('multi_hit:2','multi_hit:4'):
            issue=dict(phase='effect',category='trigger',operator=dict(domain='timing',descriptor=descriptor))
            r=reference_readiness(issue);m=r['declared_logical_actor_geometry_metal_validation']
            self.assertEqual(m['evidence_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual((m['inputs'],m['native_cases']),(audit['input_count'],audit['native_cases']))
            self.assertTrue(m['metal_verified']);self.assertFalse(m['current_cuda_verified'])
            self.assertFalse(m['default_producer_installed']);self.assertEqual(r['lane'],'reference_model_gap')
            self.assertFalse(r['gpu_supported']);self.assertFalse(r['full_character_verified'])

if __name__=='__main__':unittest.main()
