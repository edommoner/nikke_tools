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


if __name__=='__main__':unittest.main()
