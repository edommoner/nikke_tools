"""Independent sealing must use a fresh comparison exactly once, never old JSON."""
import os,hashlib,json,tempfile,subprocess
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('seal_test_cli',ROOT/'scripts/nikke_gpu.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class SealTests(unittest.TestCase):
    def test_seal_budget_rejects_invalid_values_before_child_or_io(self):
        for timeout in (0,-1,181,True,1.5,'90'):
            with self.subTest(timeout=timeout),patch.object(cli.subprocess,'run') as run,self.assertRaisesRegex(ValueError,'CPU seal timeout'):
                cli.seal_development(Path('unused'),Path('unused'),Path('unused'),timeout=timeout)
            run.assert_not_called()
    def test_original_comparison_runs_once_and_is_used_without_changes(self):
        result=dict(entries=[dict(native_sha256='fresh')],calculation_verified=True)
        compare=Mock(return_value=result)
        module=SimpleNamespace(compare_readback=compare)
        audit=dict(calculation_verified=True)
        def audited(capture):
            self.assertEqual(capture,'capture')
            self.assertIs(module.compare_readback('manifest',capture),result)
            return audit
        module.audit_capture=audited
        actual,comparison=cli.audited_comparison(module,'capture')
        self.assertIs(actual,audit);self.assertIs(comparison,result)
        compare.assert_called_once_with('manifest','capture')
        self.assertIs(module.compare_readback,compare)

    def test_old_report_or_multiple_comparisons_cannot_be_sealed(self):
        for calls,passed in ((0,True),(2,True),(1,False)):
            compare=Mock(return_value=dict(calculation_verified=passed))
            module=SimpleNamespace(compare_readback=compare)
            def audit(capture):
                for _ in range(calls):module.compare_readback('manifest',capture)
                return dict(calculation_verified=passed)
            module.audit_capture=audit
            with self.subTest(calls=calls,passed=passed),self.assertRaisesRegex(ValueError,'exactly one'):
                cli.audited_comparison(module,'capture')
            self.assertEqual(compare.call_count,calls);self.assertIs(module.compare_readback,compare)

    def test_comparator_failure_is_preserved_and_binding_restored(self):
        compare=Mock(side_effect=ValueError('Raw mismatch'))
        module=SimpleNamespace(compare_readback=compare)
        module.audit_capture=lambda capture:module.compare_readback('manifest',capture)
        with self.assertRaisesRegex(ValueError,'Raw mismatch'):cli.audited_comparison(module,'capture')
        self.assertIs(module.compare_readback,compare)


    def test_independent_seal_uses_package_relative_oracle_from_another_checkout(self):
        # Old research adapters contain relative spec_from_file_location paths.
        # Use a real child interpreter and different oracles in both checkouts.
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);package=base/'package';other=base/'other';capture=base/'capture'
            for root in (package,other):
                (root/'research').mkdir(parents=True);(root/'gpu').mkdir()
                (root/'gpu/proof.slang').write_text('same GPU source')
            (package/'research/oracle.py').write_text("LABEL='package'\n")
            (other/'research/oracle.py').write_text("LABEL='other'\n")
            digest=hashlib.sha256((package/'gpu/proof.slang').read_bytes()).hexdigest()
            (package/'scripts').mkdir();capture.mkdir();(capture/'run.json').write_text('{"backend":"metal"}')
            fake="""import json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path):return json.loads(path.read_text())
def verify_package(root):return dict(package_id='frozen',purpose='development',golden=dict(source_sha256={'gpu/proof.slang':DIGEST}))
def is_development(manifest):return manifest['purpose']=='development'
def compare_readback(capture):
    label=runpy.run_path('research/oracle.py')['LABEL']
    if label!='package':raise ValueError('Imported oracle from another checkout')
    return dict(input_sha256='input',output_sha256='output',entries=[dict(name=label)],generated_normalized={},calculation_verified=True)
def audit_capture(capture):
    compare_readback(capture)
    return dict(calculation_verified=True)
""".replace('DIGEST',repr(digest))
            (package/'scripts/nikke_gpu.py').write_text(fake)
            output=base/'sealed.json'
            previous=Path.cwd()
            try:
                os.chdir(other)
                with patch.object(cli,'ROOT',other),patch.object(cli.subprocess,'run',wraps=subprocess.run) as child:
                    result=cli.seal_development(package,capture,output,timeout=90)
                    self.assertEqual(child.call_args.kwargs['timeout'],90)
            finally:os.chdir(previous)
            self.assertTrue(result['sealed']);self.assertEqual(result['gpu_calls'],0)
            self.assertEqual(json.loads(output.read_text())['entries'],[dict(name='package')])
            (package/'scripts/nikke_gpu.py').write_text(fake.replace("purpose='development'","purpose='sealed'"))
            with patch.object(cli,'ROOT',other):
                audited=cli.audit_saved_metal(package,capture,timeout=90)
                self.assertEqual(audited['package_id'],'frozen')
                with self.assertRaises(subprocess.CalledProcessError):cli.seal_development(package,capture,base/'not-development.json',timeout=90)
            self.assertFalse((base/'not-development.json').exists())


if __name__=='__main__':unittest.main()
