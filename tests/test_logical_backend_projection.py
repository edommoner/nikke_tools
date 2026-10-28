"""A composed transport inverse accepts only its exact audited output."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_logical_geometry_source_contract import project_backend_source,project_sources


class LogicalBackendProjectionTests(unittest.TestCase):
    def test_exact_inverse_output_is_idempotent_for_composed_callers(self):
        once=project_backend_source(ROOT)
        self.assertEqual(project_backend_source(ROOT,once),once)
        self.assertEqual(project_sources(ROOT,{'app/portable_backend.py':once})['app/portable_backend.py'],once)
        row=json.loads((ROOT/'tests/fixtures/portable-logical-geometry-source-delta.json').read_text())['files']['app/portable_backend.py']
        self.assertEqual(__import__('hashlib').sha256(once.encode()).hexdigest(),row['before_sha256'])

    def test_current_and_historical_transport_tampering_are_rejected(self):
        for source in ((ROOT/'app/portable_backend.py').read_text(),project_backend_source(ROOT)):
            with self.subTest(historical=source.startswith('# historical')),self.assertRaises((AssertionError,ValueError)):
                project_backend_source(ROOT,source+'\n')

    def test_historical_fast_path_checks_the_forward_anchor_too(self):
        once=project_backend_source(ROOT)
        ledger=json.loads((ROOT/'tests/fixtures/portable-logical-geometry-source-delta.json').read_text())
        ledger=copy.deepcopy(ledger);ledger['files']['app/portable_backend.py']['after_sha256']='0'*64
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'tests/fixtures/portable-logical-geometry-source-delta.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(ledger))
            with self.assertRaisesRegex(ValueError,'anchor differs'):project_backend_source(root,once)

    def test_current_ammo_and_resource_certificates_keep_complete_legacy_outputs(self):
        import hashlib
        sys.path.insert(0,str(ROOT/'scripts'));import nikke_gpu
        from portable_backend import source_hashes
        for key,count in [('ammo',4),('resources',3)]:
            suite='coordinate-original-'+key;config=nikke_gpu.SUITES[suite]
            raw=(ROOT/config['golden']).read_bytes();current=json.loads(raw)
            old=json.loads((ROOT/('research/portable-'+suite+'-short-expected.json')).read_text())
            proof=json.loads((ROOT/('tests/fixtures/original-'+key+'-current-independent-v2.json')).read_text())
            certificate=json.loads((ROOT/nikke_gpu.SUITES['compiler-full--'+suite]['golden']).read_text())
            self.assertEqual(current['source_sha256'],source_hashes(config['source']))
            self.assertEqual(current['entries'],old['entries']);self.assertEqual(current['output_sha256'],old['output_sha256'])
            self.assertEqual(certificate['baseline_golden_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(certificate['source_sha256'],current['source_sha256'])
            self.assertTrue(proof['calculation_verified']);self.assertEqual((proof['input_count'],proof['native_cases'],proof['gpu_calls']),(count,count,0))
            self.assertEqual(proof['output_sha256'],current['output_sha256'])


if __name__=='__main__':unittest.main()
