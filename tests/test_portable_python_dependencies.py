"""Dependency failures are explicit, local, and detected without installation."""
import importlib.metadata,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import portable_python_dependencies as deps

class DependencyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/deps.REQUIREMENTS_FILE).write_text('# Independent oracle\ngmpy2==2.2.1\n')
        self.patterns=['test_coordinate_landing_v1.py']
    def test_unrelated_tests_do_not_inspect_or_import_oracle(self):
        with patch.object(deps.importlib.metadata,'version',side_effect=AssertionError),patch.object(deps.importlib,'import_module',side_effect=AssertionError):r=deps.check(self.root,['test_typed_geometry.py'])
        self.assertTrue(r['passed']);self.assertEqual(r['dependencies'],[])
    def test_missing_package_does_not_attempt_import(self):
        with patch.object(deps.importlib.metadata,'version',side_effect=importlib.metadata.PackageNotFoundError),patch.object(deps.importlib,'import_module',side_effect=AssertionError):r=deps.check(self.root,self.patterns)
        self.assertFalse(r['passed']);self.assertEqual(r['dependencies'][0]['issue'],'missing_distribution');self.assertFalse(r['installation_performed']);self.assertEqual(r['gpu_calls'],0)
    def test_wrong_version_is_rejected_before_import(self):
        with patch.object(deps.importlib.metadata,'version',return_value='2.3.0'),patch.object(deps.importlib,'import_module',side_effect=AssertionError):r=deps.check(self.root,self.patterns)
        self.assertEqual(r['dependencies'][0]['issue'],'version_mismatch');self.assertFalse(r['passed'])
    def test_broken_extension_is_not_a_dependency_success(self):
        with patch.object(deps.importlib.metadata,'version',return_value='2.2.1'),patch.object(deps.importlib,'import_module',side_effect=ImportError('DLL unavailable')):r=deps.check(self.root,self.patterns)
        self.assertFalse(r['passed']);self.assertEqual(r['dependencies'][0]['issue'],'import_failed')
    def test_exact_importable_pin_records_its_path(self):
        module=SimpleNamespace(__file__='/private/deps/gmpy2.pyd',version=lambda:'2.2.1',mpfr_version=lambda:'MPFR 4.2.1')
        with patch.object(deps.importlib.metadata,'version',return_value='2.2.1'),patch.object(deps.importlib,'import_module',return_value=module):r=deps.check(self.root,self.patterns)
        self.assertTrue(r['passed']);self.assertEqual(r['dependencies'][0]['module_path'],module.__file__)
    def test_metadata_cannot_hide_a_different_imported_module(self):
        module=SimpleNamespace(__file__='/other/gmpy2.pyd',version=lambda:'2.3.0',mpfr_version=lambda:'MPFR 4.2.1')
        with patch.object(deps.importlib.metadata,'version',return_value='2.2.1'),patch.object(deps.importlib,'import_module',return_value=module):r=deps.check(self.root,self.patterns)
        self.assertFalse(r['passed']);self.assertEqual(r['dependencies'][0]['issue'],'import_version_mismatch')
    def test_unpinned_or_url_requirement_is_rejected(self):
        for text in ['gmpy2>=2.2.1','gmpy2 @ https://example.invalid/wheel','gmpy2==2.2.1\ngmpy2==2.2.1','']:
            (self.root/deps.REQUIREMENTS_FILE).write_text(text)
            with self.assertRaises(ValueError):deps.check(self.root,self.patterns)
    def test_run_preflight_stops_before_cpu_worker_when_missing(self):
        sys.path.insert(0,str(ROOT/'scripts'));import nikke_gpu as cli
        (self.root/'tests').mkdir();(self.root/'tests'/self.patterns[0]).write_text('')
        capture=self.root/'capture';capture.mkdir()
        manifest=dict(suite='probe',files=[dict(path=deps.REQUIREMENTS_FILE)])
        with patch.object(cli,'ROOT',self.root),patch.object(cli,'SUITES',dict(probe=dict(tests=self.patterns))),patch.object(deps.importlib.metadata,'version',side_effect=importlib.metadata.PackageNotFoundError),patch.object(cli.subprocess,'run',side_effect=AssertionError('Worker must not start')):
            with self.assertRaisesRegex(ValueError,'Validation Python dependencies unavailable'):cli.cpu_test_groups(manifest,capture)
        report=json.loads((capture/'python-dependencies.json').read_text())
        self.assertFalse(report['passed']);self.assertEqual(report['gpu_calls'],0);self.assertFalse((capture/'cpu-tests.json').exists())

if __name__=='__main__':unittest.main()
